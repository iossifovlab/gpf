#!/bin/env python
from __future__ import print_function
from __future__ import unicode_literals

from builtins import zip
from builtins import str
from builtins import range
from builtins import object
from future import standard_library
standard_library.install_aliases()  # noqa

from configparser import ConfigParser
import os
import sys
from numpy.lib.npyio import genfromtxt
import numpy as np
# from pprint import pprint
from collections import defaultdict
# from collections import Counter
import copy
import gzip
import pysam
import glob
from os.path import dirname
# from os.path import basename
import tempfile
import re
from GeneTerms import GeneTerms
from itertools import groupby
from VariantAnnotation import get_effect_types_set
# import itertools
from RegionOperations import Region, collapse
import operator
import pickle
import logging
from Variant import Variant, mat2Str, filter_gene_effect, str2Mat,\
    present_in_child_filter,\
    denovo_present_in_parent_filter, \
    filter_by_status, chromosome_prefix
from Family import Family, Person
from transmitted.base_query import TransmissionConfig
from transmitted.mysql_query import MysqlTransmittedQuery
from transmitted.legacy_query import TransmissionLegacy
from variant_db.variant_query import VariantQuery
from pheno.common import Role, Status, Gender

LOGGER = logging.getLogger(__name__)

CHROMOSOME_PREFIX = None


def regions_matcher(regions):
    if isinstance(regions, list):
        regs = regions
    else:
        regs = regions.split(',')
    reg_defs = []

    for r in regs:
        smcP = r.find(":")
        dsP = r.find("-")
        chrom = r[0:smcP]
        if CHROMOSOME_PREFIX not in chrom:
            chrom = CHROMOSOME_PREFIX + chrom
        beg = int(r[smcP + 1:dsP])
        end = int(r[dsP + 1:])
        reg_defs.append((chrom, beg, end))

    return lambda vchr, vpos: \
        any([(chrom == vchr and
              vpos >= beg and
              vpos <= end)
             for(chrom, beg, end) in reg_defs])


class StudyGroup(object):

    def __init__(self, vdb, name):
        self.vdb = vdb
        self.name = name
        self._configSection = 'studyGroup.' + name

        self.description = ""
        if self.vdb._config.has_option(self._configSection, 'description'):
            self.description = self.vdb._config.get(
                self._configSection, 'description')

        self.studyNames = [
            st.strip() for st in self.vdb._config.get(
                self._configSection, 'studies').split(",")
        ]

    def get_attr(self, attName):
        if self.vdb._config.has_option(self._configSection, attName):
            return self.vdb._config.get(self._configSection, attName)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)


class Study(object):

    def __init__(self, vdb, name):
        self.vdb = vdb
        self.name = name
        self._configSection = 'study.' + name
        self._dnvData = {}
        self.transmission_impl = {}

        self.has_denovo = self.vdb._config.has_option(
            self._configSection, 'denovoCalls.files')
        self.has_transmitted = self.vdb._config.has_option(
            self._configSection, 'transmittedVariants.format') or \
            self.vdb._config.has_option(
                self._configSection, 'transmittedVariants.indexFile')

        self.description = ""
        if self.vdb._config.has_option(self._configSection, 'description'):
            self.description = self.vdb._config.get(
                self._configSection, 'description')

        self.phenotypes = []
        if self.vdb._config.has_option(self._configSection, 'study.phenotype'):
            phenotypes = self.vdb._config.get(
                self._configSection, 'study.phenotype')
            self.phenotypes = [p.strip() for p in phenotypes.split(',')]

        self.phdb = None

        self._families = None
        self._badFamilies = None

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self.name)

    def get_targeted_genes(self):
        if not self.vdb._config.has_option(self._configSection, "targetedGenes"):
            return
        tGsFN = self.vdb._config.get(self._configSection, "targetedGenes")
        tGsF = open(tGsFN)
        tgsS = {l.strip() for l in tGsF}
        tGsF.close()
        return tgsS

    def has_attr(self, attName):
        return self.vdb._config.has_option(self._configSection, attName)

    def get_attr(self, attName):
        if self.has_attr(attName):
            return self.vdb._config.get(self._configSection, attName)

    def types(self):
        if self.has_attr('study.type'):
            return self.get_attr('study.type').split(',')
        return []

    def _get_transmitted_impl(self, callSet):
        if callSet not in self.transmission_impl:
            conf = TransmissionConfig(self, callSet)
            impl_format = conf._get_params("format") or 'legacy'

            if impl_format is None or impl_format == 'legacy':
                self.transmission_impl[callSet] = \
                    TransmissionLegacy(self, callSet)
            elif impl_format == 'mysql':
                self.transmission_impl[callSet] = \
                    MysqlTransmittedQuery(self, callSet)
            elif impl_format == 'new_mysql':
                self.transmission_impl[callSet] = \
                    VariantQuery(self)
            else:
                raise Exception("unexpected transmission format")

        impl = self.transmission_impl[callSet]
        return impl

    def get_transmitted_variants(self, callSet='default', **kwargs):
        LOGGER.info("get_transmitted_variants: %s", kwargs)
        impl = self._get_transmitted_impl(callSet)
        vs = impl.get_transmitted_variants(**kwargs)
        for v in vs:
            yield v

    def get_families_with_transmitted_variants(self,
                                               callSet='default', **kwargs):
        LOGGER.debug("get_families_with_transmitted_variants: %s", kwargs)
        impl = self._get_transmitted_impl(callSet)
        fs = impl.get_families_with_transmitted_variants(**kwargs)
        for f in fs:
            yield f

    def get_transmitted_summary_variants(self, callSet='default', **kwargs):
        impl = self._get_transmitted_impl(callSet)
        vs = impl.get_transmitted_summary_variants(**kwargs)
        for v in vs:
            yield v

    def genomic_scores_filter(self, variant, genomicScores):
        try:
            return all([score['min'] <= float(variant.atts[score['metric']])
                        < score['max']
                        for score in genomicScores])
        except ValueError:
            return False
        except KeyError:
            return False
        return False

    def get_denovo_variants(self, inChild=None, presentInChild=None,
                            presentInParent=None, genomicScores=[],
                            gender=None, roles=None, status=None,
                            variantTypes=None, effectTypes=None, geneSyms=None,
                            familyIds=None, regionS=None, callSet=None,
                            limit=None):
        picFilter = present_in_child_filter(presentInChild, gender)
        pipFilter = denovo_present_in_parent_filter(presentInParent)

        geneSymsUpper = None
        if geneSyms is not None:
            geneSymsUpper = [sym.upper() for sym in geneSyms]

        if isinstance(effectTypes, str):
            effectTypes = self.vdb.effectTypesSet(effectTypes)

        if isinstance(variantTypes, str):
            variantTypes = set(variantTypes.split(","))

        reg_matcher = None
        if regionS:
            reg_matcher = regions_matcher(regionS)

        dnvData = self._load_dnv_data(callSet)

        for v in dnvData:
            if familyIds and v.familyId not in familyIds:
                continue
            if not self.genomic_scores_filter(v, genomicScores):
                continue
            if pipFilter and not pipFilter(v.fromParentS):
                continue
            if picFilter and not picFilter(v.inChS):
                continue
            elif inChild and inChild not in v.inChS:
                continue

            if variantTypes and all([not v.variant.startswith(vt) for vt in variantTypes]):
                continue
            if reg_matcher:
                smcP = v.location.find(":")
                vChr = v.location[0:smcP]
                try:
                    vPos = v.location[smcP + 1:]
                    if '-' in vPos:
                        p1, p2 = vPos.split('-')
                        p1 = int(p1)
                        p2 = int(p2)
                        if not (reg_matcher(vChr, p1) or
                                reg_matcher(vChr, p2)):
                            continue
                    else:
                        p = int(vPos)
                        if not reg_matcher(vChr, p):
                            continue
                except ValueError:
                    continue

            if roles:
                roles_in_order = [m.role for m in v.memberInOrder]

                if not any(role in roles and len(v.bestSt) > 1 and
                           v.bestSt[1][i] > 0
                           for i, role in enumerate(roles_in_order)):
                    continue

            if status:
                if filter_by_status(v, status):
                    continue

            if effectTypes is not None or geneSymsUpper is not None:
                requestedGeneEffects = filter_gene_effect(
                    v.geneEffect, effectTypes, geneSymsUpper)
                if not requestedGeneEffects:
                    continue
                vc = copy.copy(v)
                vc._requestedGeneEffect = requestedGeneEffects

                yield vc
            else:
                yield v

    def _load_dnv_data(self, callSetP=None):
        callSet = "default"
        propName = "denovoCalls.files"

        if callSetP:
            callSet = callSetP
            propName = "denovoCalls." + callSet + ".files"

        if callSet in self._dnvData:
            return self._dnvData[callSet]

        flsS = self.vdb._config.get(self._configSection, propName)
        varList = []
        for fl in flsS.split('\n'):

            def float_conv(x):
                try:
                    return float(x or np.nan)
                except:
                    return np.nan
            print("Loading file {} for collection {}".format(fl, self.name),
                  file=sys.stderr)
            dt = genfromtxt(fl, delimiter='\t', dtype=None, names=True,
                            case_sensitive=True, deletechars='',
                            converters={"SSC-freq": float_conv,
                                        "EVS-freq": float_conv,
                                        "E65-freq": float_conv},
                            encoding='utf-8')
            if len(dt.shape) == 0:
                dt = dt.reshape(1)
            col_names = [cn.strip("#") for cn in dt.dtype.names]

            hasCenter = 'center' in col_names
            for vr in dt:
                atts = {x: vr[x] for x in col_names}
                if not hasCenter:
                    atts['center'] = "CSHL"

                v = Variant(atts, bestStColSep=" ")
                v.popType = "denovo"
                v.study = self
                varList.append(v)

        self._dnvData[callSet] = varList
        return varList

    @property
    def families(self):
        if self._families is None:
            self._load_family_data()
        return self._families

    @property
    def badFamilies(self):
        if self._badFamilies is None:
            self._load_family_data()
        return self._badFamilies

    def _load_family_data(self):
        if not self.vdb._config.has_option(
                self._configSection, "familyInfo.file"):
            self._families = {}
            return
        fdFile = self.vdb._config.get(self._configSection, "familyInfo.file")
        fdFormat = self.vdb._config.get(
            self._configSection, "familyInfo.fileFormat")

        fmMethod = {
            "quadReportSSC": self._load_family_data_from_quad_report,
            "simple": self._load_family_data_from_simple,
            "pickle": self._load_family_data_from_pickle,
            "pedigree": self._load_family_data_from_pedigree,
            "StateWE2012-data1-format": self._load_family_data_from_StateWE2012_data1,
            "EichlerWE2012-SupTab1-format": self._load_family_data_from_EichlerWE2012_SupTab1,
            "DalyWE2012-SD-Trios": self._load_family_data_from_DalyWE2012_SD_Trios,
            "SSCTrios-format": self._load_family_data_SSCTrios,
            "SSCFams-format": self._load_family_data_SSCFams,
            "IossifovWE2014": self._load_family_data_from_IossifovWE2014_families
        }

        if fdFormat not in fmMethod:
            raise Exception("Unknown Family File Format: " + fdFormat)
        print("Loading family data from: {} for collection {}".format(
            fdFile, self.name), file=sys.stderr)

        self._families, self._badFamilies = fmMethod[fdFormat](fdFile)

        if len(self.phenotypes) != 1:
            for fam in list(self._families.values()):
                for p in fam.memberInOrder:
                    p.phenotype = p.atts['phenotype']
            return
        phenotype = self.phenotypes[0]
        for fam in list(self._families.values()):
            fam.phenotype = phenotype
            fam.atts['phenotype'] = phenotype

            for p in fam.memberInOrder:
                if hasattr(p, 'status'):
                    if p.status == Status.affected:
                        p.phenotype = phenotype
                    else:
                        p.phenotype = 'unaffected'
                # FIXME: legacy affected/unaffected
                else:
                    if p.role == Role.prb:
                        p.status = Status.affected
                        p.phenotype = phenotype
                    else:
                        p.status = Status.unaffected
                        p.phenotype = 'unaffected'

                p.atts['phenotype'] = p.phenotype

    def _load_family_data_SSCFams(self, reportF):
        rf = open(reportF)
        families = {l.strip(): Family() for l in rf}
        for f in list(families.values()):
            f.memberInOrder = []

        rlsMp = {"mother": Role.mom, "father": Role.dad, "proband": Role.prb,
                 "designated-sibling": Role.sib, "other-sibling": Role.sib}
        genderMap = {"female": Gender.F, "male": Gender.M}

        for indS in list(self.vdb.sfariDB.individual.values()):
            if indS.familyId not in families:
                continue
            p = Person()
            p.personId = indS.personId
            p.gender = genderMap[indS.sex]
            p.role = rlsMp[indS.role]
            families[indS.familyId].memberInOrder.append(p)
        return families, {}

    def _load_family_data_SSCTrios(self, reportF):
        buff = defaultdict(dict)
        for _indId, indS in list(self.vdb.sfariDB.individual.items()):
            if indS.collection != "ssc":
                continue
            buff[indS.familyId][indS.role] = indS

        rlsMp = list(zip(
            "mother,father,proband".split(','),
            [Role.mom, Role.dad, Role.prb]
        ))
        genderMap = {"female": Gender.F, "male": Gender.M}

        families = {}
        for fid, rls in buff.items():
            if "mother" not in rls or "father" not in rls or "proband" not in rls:
                continue
            f = Family()
            f.familyId = fid
            f.memberInOrder = []

            for srl, irl in rlsMp:
                p = Person()
                p.personId = rls[srl].personId
                p.gender = genderMap[rls[srl].sex]
                p.role = irl
                f.memberInOrder.append(p)
            families[f.familyId] = f
        return families, {}

    @staticmethod
    def _load_family_data_from_pickle(fn):
        result = pickle.load(open(fn, "rb"))
        for families in result:
            for family in list(families.values()):
                for member in family.memberInOrder:
                    if not isinstance(member.role, str):
                        member.role = member.role.decode("UTF-8")
                    if not isinstance(member.gender, str):
                        member.gender = member.gender.decode("UTF-8")

        # FIXME: this should be done when the pickles are generated
        for family_dict in result:
            for family in family_dict.items():
                for member in family[1].memberInOrder:
                    member.role = Role[member.role] \
                        if member.role in Role.__members__ \
                        else member.role
                    member.gender = Gender[member.gender] \
                        if member.gender in Gender.__members__ \
                        else member.gender
                    if hasattr(member, 'status'):
                        member.status = Status[member.status] \
                            if member.role in Status.__members__ \
                            else member.status
        # print(result)
        return result

    @staticmethod
    def gender_converter(gender):
        return Gender(int(gender))

    @staticmethod
    def gender_converter_by_name(gender_name):
        return Gender[gender_name]

    @staticmethod
    def gender_converter_by_name_or_value(gender_name_or_value):
        if gender_name_or_value in Gender.__members__:
            return Gender[gender_name_or_value]
        # raise ValueError('not standard gender: {}'.format(gender_name_or_value))
        return Gender(int(gender_name_or_value))

    @staticmethod
    def role_converter(role):
        if role in Role.__members__:
            return Role[role]
        raise ValueError("Unknown role {}, defaulting to unknown".format(role))

    @staticmethod
    def status_converter(status):
        return Status(int(status))

    @staticmethod
    def _load_family_data_from_simple(reportF):
        dt = genfromtxt(reportF, delimiter='\t', dtype=None,
                        names=True, case_sensitive=True,
                        comments="asdgasdgasdga", encoding='utf-8', 
			converters={
				'role': Study.role_converter,
				'status': Study.status_converter,
				'gender': Study.gender_converter_by_name_or_value
			})
        families = defaultdict(Family)
        for dtR in dt:
            fmId = str(dtR['familyId'])
            families[fmId].familyId = fmId
            atts = {x: dtR[x] for x in dt.dtype.names}
            families[fmId].atts.update(atts)
            p = Person(atts)
            p.personId = str(atts['personId'])
            p.gender = str(atts['gender'])
            p.role = str(atts['role'])
            try:
                families[fmId].memberInOrder.append(p)
            except AttributeError:
                families[fmId].memberInOrder = [p]
        return families, {}

    @staticmethod
    def _load_family_data_from_pedigree(family_file):
        id_converter = lambda x: x if x != '0' else ''

        dt = genfromtxt(
            family_file, delimiter='\t', dtype=None, names=True,
            case_sensitive=True, comments="asdgasdgasdga",
            converters={
                'momId': id_converter,
                'dadId': id_converter,
                'role': Study.role_converter,
                'status': Study.status_converter,
                'gender': Study.gender_converter_by_name_or_value
            })
        families = defaultdict(Family)
        for dtR in dt:
            fmId = str(dtR['familyId'])
            families[fmId].familyId = fmId
            atts = {x: dtR[x] for x in dt.dtype.names}

            assert 'personId' in atts
            assert 'gender' in atts
            assert 'role' in atts
            assert 'momId' in atts
            assert 'dadId' in atts
            assert 'status' in atts

            p = Person(atts)
            for key, item in atts.items():
                setattr(p, key, item)

            families[fmId].memberInOrder.append(p)

        return families, {}

    @staticmethod
    def _load_family_data_from_DalyWE2012_SD_Trios(reportF):
        families = {}

        dt = genfromtxt(reportF, delimiter='\t', dtype=None,
                        names=True, case_sensitive=True,
                        comments="asdgasdgasdga", encoding='utf-8'
        )

        genderDecoding = {"female": Gender.F, "male": Gender.M}

        for dtR in dt:
            atts = {x: dtR[x] for x in dt.dtype.names}
            prb = Person(atts)
            prb.gender = genderDecoding[dtR["Gender"]]
            prb.role = Role.prb
            prb.personId = dtR["Child_ID"]

            fid = prb.personId

            mom = Person()
            mom.personId = fid + ".mo"
            mom.role = Role.mom
            mom.gender = Gender.F

            dad = Person()
            dad.personId = fid + ".fa"
            dad.role = Role.dad
            dad.gender = Gender.M

            f = Family()
            f.familyId = fid
            f.memberInOrder = [mom, dad, prb]

            families[fid] = f
        return families, {}

    def _load_family_data_from_EichlerWE2012_SupTab1(self, reportF):
        famBuff = defaultdict(dict)
        dt = genfromtxt(reportF, delimiter='\t', dtype=None,
                        names=True, case_sensitive=True,
                        comments="asdgasdgasdga", encoding='utf-8'
        )

        genderDecoding = {"female": Gender.F, "male": Gender.M}
        roleDecoding = {"SSC189": Role.prb, "SSC189_Sib": Role.sib,
                        "Pilot_Pro": Role.prb, "Pilot_Sib": Role.sib}

        for dtR in dt:
            atts = {x: dtR[x] for x in dt.dtype.names}
            p = Person(atts)
            p.gender = genderDecoding[dtR["sex"]]
            p.role = roleDecoding[dtR["type"]]
            p.personId = dtR["child"]

            pid = p.personId
            fid = pid[0:pid.find('.')]

            famBuff[fid][p.role.name] = p

        families = {}
        for fid, pDct in famBuff.items():
            f = Family()
            f.familyId = fid

            mom = Person()
            mom.personId = fid + ".mo"
            mom.role = Role.mom
            mom.gender = Gender.F

            dad = Person()
            dad.personId = fid + ".fa"
            dad.role = Role.dad
            dad.gender = Gender.M

            if len(pDct) == 1:
                f.memberInOrder = [mom, dad, pDct[Role.prb.name]]
            elif len(pDct) == 2:
                f.memberInOrder = \
                    [mom, dad, pDct[Role.prb.name], pDct[Role.sib.name]]
            else:
                raise Exception(
                    "Weird family: " + fid + " with " + str(len(pDct)) + " memmbers")

            families[fid] = f

        return families, {}

    def _load_family_data_from_StateWE2012_data1(self, reportF):
        famBuff = defaultdict(dict)
        badFamBuff = defaultdict(dict)
        dt = genfromtxt(reportF, delimiter='\t', dtype=None,
                        names=True, case_sensitive=True,
                        comments="asdgasdgasdga", encoding='utf-8'
        )

        genderDecoding = {"Male": Gender.M, "Female": Gender.F}
        roleDecoding = {"Mother": Role.mom, "Father": Role.dad,
                        "Affected_proband": Role.prb, "Unaffected_Sibling": Role.sib}

        for dtR in dt:
            atts = {x: dtR[x] for x in dt.dtype.names}
            p = Person(atts)
            p.gender = genderDecoding[dtR["Gender"]]
            p.role = roleDecoding[dtR["Role"]]
            p.personId = dtR["Sample"]

            if dtR['Sample_PassFail'] == 'Fail' or dtR['Family_PassFail'] == 'Fail':
                badFamBuff[str(dtR["Family"])][p.role.name] = p
            else:
                famBuff[str(dtR["Family"])][p.role.name] = p

        families = {}
        for fid, pDct in famBuff.items():
            f = Family()
            f.familyId = fid

            if len(pDct) == 3:
                f.memberInOrder = \
                    [pDct[Role.mom.name], pDct[Role.dad.name], pDct[Role.prb.name]]
            elif len(pDct) == 4:
                f.memberInOrder = [
                    pDct[Role.mom.name], pDct[Role.dad.name],
                    pDct[Role.prb.name], pDct[Role.sib.name]
                ]
            else:
                raise Exception(
                    "Weird family: " + fid + " with " + str(len(pDct)) + " memmbers")

            families[fid] = f

        badFamilies = {}
        for fid, pDct in badFamBuff.items():
            f = Family()
            f.familyId = fid

            f.memberInOrder = pDct.values()

            badFamilies[fid] = f

        return families, badFamilies

    def _load_family_data_from_IossifovWE2014_families(self, reportF):
        families = {}
        badFamilies = {}
        qrp = genfromtxt(
            reportF, delimiter='\t', dtype=None, names=True,
            case_sensitive=True, encoding='utf-8'
        )
        for qrpR in qrp:
            f = Family()
            f.familyId = str(qrpR['familyId'])

            f.atts = {x: qrpR[x] for x in qrp.dtype.names}

            fCntrs = set()
            chldSfx = defaultdict(set)
            for saA in qrpR.dtype.names:
                if not saA.startswith('SequencedAt'):
                    continue
                cntr = saA[len('SequencedAt'):]
                cntrChldS = qrpR[saA]
                if not cntrChldS:
                    continue
                for sfx in cntrChldS.split(","):

                    fCntrs.add(cntr)
                    chldSfx[sfx.strip('"')].add(cntr)
            fmCntrS = ",".join(sorted(fCntrs))
            f.atts['centers'] = fmCntrS

            mom = Person()
            mom.personId = f.familyId + ".mo"
            mom.role = Role.mom
            mom.gender = Gender.F
            mom.atts['race'] = qrpR['motherRace']
            mom.atts['centers'] = fmCntrS

            dad = Person()
            dad.personId = f.familyId + ".fa"
            dad.role = Role.dad
            dad.gender = Gender.M
            dad.atts['race'] = qrpR['fatherRace']
            dad.atts['centers'] = fmCntrS

            f.memberInOrder = [mom, dad]

            sfxC2Role = {'p': Role.prb, 's': Role.sib}
            sfxC2GenderAt = {'p': 'probandGender', 's': 'siblingGender'}
            for sfx, chCntrs in sorted(chldSfx.items()):
                chl = Person()
                chl.personId = f.familyId + "." + sfx
                chl.role = sfxC2Role[sfx[0]]
                chl.gender = Gender[qrpR[sfxC2GenderAt[sfx[0]]]]
                chl.atts['centers'] = ",".join(sorted(chCntrs))
                f.memberInOrder.append(chl)

            families[f.familyId] = f

            '''
            # HERE

            ch1 = Person()
            ch1.personId = piF(qrpR['child1sample_id'])
            ch1.role = rlsMap[qrpR['child1role']]
            ch1.gender = qrpR['child1gender']
            transferPersonAtts(ch1,"child1")


            if qrpR['child2sample_id']:
                ch2 = Person()
                ch2.personId = piF(qrpR['child2sample_id'])
                ch2.role = rlsMap[qrpR['child2role']]
                ch2.gender = qrpR['child2gender']
                transferPersonAtts(ch2,"child2")
                f.memberInOrder.append(ch2)
            if qrpR['status'] == 'OK':
                families[f.familyId] = f
            else:
                badFamilies[f.familyId] = f
            '''
        return families, badFamilies

    def _load_family_data_from_quad_report(self, reportF):
        familyIdRE = re.compile('^auSSC(\d\d\d\d\d)')
        rlsMap = {"self": Role.prb, "sibling": Role.sib}
        families = {}
        badFamilies = {}
        qrp = genfromtxt(
            reportF, delimiter='\t', dtype=None, names=True,
            case_sensitive=True, encoding='utf-8'
        )
        for qrpR in qrp:
            f = Family()
            f.familyId = qrpR['quadquad_id']
            if familyIdRE.match(f.familyId):
                f.familyId = f.familyId[5:10]

            f.atts = {x: qrpR[x] for x in qrp.dtype.names}

            def piF(pi):
                sfariDB = self.vdb.sfariDB
                if not sfariDB:
                    return pi
                if pi not in sfariDB.sampleNumber2PersonId:
                    return pi
                return sfariDB.sampleNumber2PersonId[pi]

            def transferPersonAtts(pd, attPref):
                pd.atts['sample_id'] = qrpR[attPref + 'sample_id']
                pd.atts['mean_depth'] = qrpR[attPref + 'mean_depth']
                pd.atts['target_covered_at_1_prcnt'] = qrpR[
                    attPref + '_target_covered_at_1_prcnt']
                pd.atts['target_covered_at_10_prcnt'] = qrpR[
                    attPref + '_target_covered_at_10_prcnt']
                pd.atts['target_covered_at_20_prcnt'] = qrpR[
                    attPref + '_target_covered_at_20_prcnt']
                pd.atts['target_covered_at_40_prcnt'] = qrpR[
                    attPref + '_target_covered_at_40_prcnt']
                pd.atts['relXcopy'] = qrpR[attPref + 'relXcopy']
                pd.atts['relYcopy'] = qrpR[attPref + 'relYcopy']
                pd.atts['genderMismatchStr'] = qrpR[
                    attPref + 'genderMismatchStr']

            mom = Person()
            mom.personId = piF(qrpR['mothersample_id'])
            mom.role = Role.mom
            mom.gender = Gender.F
            transferPersonAtts(mom, "mother")

            dad = Person()
            dad.personId = piF(qrpR['fathersample_id'])
            dad.role = Role.dad
            dad.gender = Gender.M
            transferPersonAtts(dad, "father")

            ch1 = Person()
            ch1.personId = piF(qrpR['child1sample_id'])
            ch1.role = rlsMap[qrpR['child1role']]
            ch1.gender = Gender[qrpR['child1gender']]
            transferPersonAtts(ch1, "child1")

            f.memberInOrder = [mom, dad, ch1]

            if qrpR['child2sample_id']:
                ch2 = Person()
                ch2.personId = piF(qrpR['child2sample_id'])
                ch2.role = rlsMap[qrpR['child2role']]
                ch2.gender = Gender[qrpR['child2gender']]
                transferPersonAtts(ch2, "child2")
                f.memberInOrder.append(ch2)
            if qrpR['status'] == 'OK':
                families[f.familyId] = f
            else:
                badFamilies[f.familyId] = f

        return families, badFamilies


class VariantsDB(object):

    def __init__(self, daeDir,
                 confFile=None, sfariDB=None, giDB=None,
                 phDB=None, genomesDB=None,
                 data_dir=None):
        self.sfariDB = sfariDB
        self.giDB = giDB

        # self.phDB = phDB
        self.genomesDB = genomesDB

        global CHROMOSOME_PREFIX
        if CHROMOSOME_PREFIX is None:
            CHROMOSOME_PREFIX = chromosome_prefix(self.genomesDB)

        if not confFile:
            confFile = daeDir + "/variantDB.conf"

        self._config = ConfigParser({
            'wd': daeDir,
            'data': data_dir
        })
        self._config.optionxform = lambda x: x

        self._config.read(confFile)

        self._studies = {}
        for secName in self._config.sections():
            if secName.startswith('study.'):
                studyName = secName[6:]
                self._studies[studyName] = Study(self, studyName)

        self._studyGroups = {}
        for secName in self._config.sections():
            if secName.startswith('studyGroup.'):
                gName = secName[11:]
                self._studyGroups[gName] = StudyGroup(self, gName)

                for stN in self._studyGroups[gName].studyNames:
                    if stN not in self._studies:
                        raise Exception(
                            "The study " + stN + " in the study group " + gName + " is unknown")

    def get_gene_regions(self, gene_list):
        DATA = {"OSBPL8": "12:76770000-76890000",
                "DIP2C": "10:323271-532485",
                "FAM49A": "2:16725000-16780000",
                "AGPAT3": "21:4537000-45403000"}

        if not self.genomesDB:
            return

        try:
            gms = self._gms
        except AttributeError:
            gms = self.genomesDB.get_gene_models()
            self._gms = gms

        rgns = []
        for gs in gene_list:
            for gm in gms.gene_models_by_gene_name(gs):
                rgns.append(Region(gm.chr, gm.tx[0] - 200, gm.tx[1] + 200))
        if rgns:
            rgns = collapse(rgns)
        return ["%s:%d-%d" % (r.chr, r.start, r.stop) for r in rgns]

    def get_study_names(self):
        return sorted(self._studies.keys())

    def get_study_group_names(self):
        return sorted(self._studyGroups.keys())

    def get_study(self, name):
        if name in self._studies:
            return self._studies[name]
        if name in self._studyGroups:
            if len(self._studyGroups[name].studyNames) != 1:
                raise Exception(
                    'get_study can only use study groups with only one study')
            return self._studies[self._studyGroups[name].studyNames[0]]
        raise Exception('unknown study ' + name)

    def get_studies(self, definition):
        sts = []

        for name in definition.split(","):
            name = name.strip()
            if name in self._studies:
                sts.append(self._studies[name])
            if name in self._studyGroups:
                for sName in self._studyGroups[name].studyNames:
                    sts.append(self._studies[sName])
        return sts

    def get_study_group(self, gName):
        if gName not in self._studyGroups:
            raise Exception("Unknown study group " + gName)
        return self._studyGroups[gName]

    def get_denovo_variants(self, studies, **filters):
        seenVs = set()
        if isinstance(studies, str):
            studies = self.get_studies(studies)
        denovo_studies = [st for st in studies if st.has_denovo]
        if 'studyTypes' in filters:
            studyTypes = filters['studyTypes']
            studyTypes = {studyTypes} if type(studyTypes) == str else set(studyTypes)
            denovo_studies = [st for st in denovo_studies if not studyTypes.isdisjoint(st.types())]
            del filters['studyTypes']
        for study in denovo_studies:
            for v in study.get_denovo_variants(**filters):
                vKey = v.familyId + v.location + v.variant
                if vKey in seenVs:
                    continue
                yield v
                seenVs.add(vKey)

    def _parse_validation_report(self, fn, knownFams, batchId=None):
        print("Parsing validation reprt file:|{}|".format(fn),
              file=sys.stderr)
        variants = []
        dt = genfromtxt(
            fn, delimiter='\t', dtype=None, names=True, case_sensitive=True,
            encoding='utf-8'
        )
        # if there is only row of data in the file then the genfromtxt function returns a 0d array.
        # this causes an error when trying to iterate over it, so it must be
        # converted to a 1d array
        if dt.ndim == 0:
            dt = dt.reshape(1)

        if not batchId:
            batchId = dirname(fn).split("/")[-2]

        for dtR in dt:
            class ValidationVariant(object):

                @property
                def bestSt(self):
                    try:
                        return self._bestSt
                    except AttributeError:
                        self._bestSt = str2Mat(self.bestStS, colSep=" ")
                        return self._bestSt

                @property
                def valBestSt(self):
                    try:
                        return self._valBestSt
                    except AttributeError:
                        self._valBestSt = str2Mat(self.valBestStS, colSep=" ")
                        return self._valBestSt

                @property
                def valCounts(self):
                    try:
                        return self._valCounts
                    except AttributeError:
                        self._valCounts = str2Mat(self.valCountsS, colSep=" ")
                        return self._valCounts

                @property
                def inChS(self):
                    mbrs = self.memberInOrder
                    bs = self.bestSt
                    childStr = ''
                    for c in range(2, len(mbrs)):
                        if bs[1][c]:
                            childStr += (mbrs[c].role + mbrs[c].gender)
                    return childStr

            v = ValidationVariant()

            v.batchId = batchId
            v.atts = {x: dtR[x] for x in dt.dtype.names}

            v.familyId = str(dtR['familyId'])
            v.location = dtR['location']
            v.variant = dtR['variant']
            v.bestStS = dtR['bestState']
            v.resultNote = dtR['valnote']

            try:
                v.why = dtR['why']
            except:
                v.why = "???"

            try:
                v.who = dtR['who']
            except:
                v.who = "???"

            v.valCountsS = dtR['valcounts']
            v.valBestStS = dtR['valbestState']
            v.valStatus = dtR['valstatus']

            v.valParent = ""
            # if the valparent column exists but is empty, then the values
            # are turned into a boolean value not and string, if this is
            # the case then do not set the value because it will cause an
            # error
            if 'valparent' in dtR.dtype.names and dtR['valparent'].dtype != bool:
                v.valParent = dtR['valparent']

            if v.familyId in knownFams:
                v.memberInOrder = knownFams[v.familyId].memberInOrder
            else:
                v.memberInOrder = []
                print("Breh, the family{} is unknown".format(v.familyId),
                      file=sys.stderr)

            # nvf.write("\t".join((v.familyId,v.location,v.variant,v.bestStS,v.who,v.why,v.batchId,v.valCountsS,v.valBestStS,v.valStatus,v.resultNote,v.valParent)) + "\n")
            variants.append(v)
        # nvf.close()
        return variants

    def get_validation_variants(self):
        validationDir = self._config.get('validation', 'dir')
        studyNames = self._config.get('validation', 'studies')
        stdies = [self.get_study(x) for x in studyNames.split(',')]

        print("validationDir: |{}|".format(validationDir), file=sys.stderr)
        print("studyNames: |{}|".format(studyNames), file=sys.stderr)

        knownFams = {}
        for stdy in stdies:
            for f in stdy.families:
                if f in knownFams:
                    print("Ha, family {} is more that one study: "
                          "{} and {}".format(
                              f, stdy.name, knownFams[f]))
                knownFams[f] = stdy.families[f]

        # print knownFams
        '''
        knownIns = {}
        for v in self.get_denovo_variants(stdies,callSet="dirty"):
            if v.variant.startswith('ins('):
                seq = v.variant[4:-1]
                for ic in reversed(range(len(seq))):
                    if not seq[ic].isdigit():
                        break
                ic+=1
                seq = seq[0:ic]
                iLen = len(seq)

                k = "".join((v.familyId,";",v.location,";",str(iLen)))
                if k in knownIns:
                    print >>sys.stderr, 'aaaa: ' + knownIns[k] + " and " + v.variant
                knownIns[k] = v.variant


        '''

        nIncompleteIns = 0
        nCompleteIns = 0
        variants = []
        for fn in glob.glob(validationDir + '/*/reports/report*.txt'):
            variants += self._parse_validation_report(fn, knownFams)
        print("nIncompleteIns: {}".format(nIncompleteIns), file=sys.stderr)
        print("nCompleteIns: {}".format(nCompleteIns), file=sys.stderr)
        return variants

    def get_denovo_sets(self, dnvStds):
        r = GeneTerms()
        r.geneNS = "sym"

        #         def getMeasure(mName):
        #             from DAE import phDB
        #             strD = dict(zip(phDB.families, phDB.get_variable(mName)))
        #             # fltD = {f:float(m) for f,m in strD.items() if m!=''}
        #             fltD = {}
        #             for f, m in strD.items():
        #                 try:
        #                     mf = float(m)
        #                     # if mf>70:
        #                     fltD[f] = float(m)
        #                 except:
        #                     pass
        #             return fltD
        #
        #         nvIQ = getMeasure('pcdv.ssc_diagnosis_nonverbal_iq')

        def addSet(setname, genes, desc=None):
            if not genes:
                return
            if desc:
                r.tDesc[setname] = desc
            else:
                r.tDesc[setname] = setname
            for gSym in genes:
                r.t2G[setname][gSym] += 1
                r.g2T[gSym][setname] += 1

        def genes(inChild, effectTypes, inGenesSet=None):
            #       minIQ=None, maxIQ=None):
            if inGenesSet:
                vs = self.get_denovo_variants(
                    dnvStds, effectTypes=effectTypes,
                    inChild=inChild, geneSyms=inGenesSet)
            else:
                vs = self.get_denovo_variants(
                    dnvStds, effectTypes=effectTypes, inChild=inChild)
            return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}

# if not (minIQ or maxIQ):
#     return {ge['sym'] for v in vs for ge in v.requestedGeneEffects}
# if minIQ:
#     return {ge['sym'] for v in vs for ge in
#        v.requestedGeneEffects if v.familyId in nvIQ and
#            nvIQ[v.familyId] >= minIQ}
# if maxIQ:
#     return {ge['sym'] for v in vs for ge in v.requestedGeneEffects
#         if v.familyId in nvIQ and nvIQ[v.familyId] < maxIQ}

        def set_genes(geneSetDef):
            gtId, tmId = geneSetDef.split(":")
            return set(self.giDB.getGeneTerms(gtId).t2G[tmId].keys())

        def recSingleGenes(inChild, effectTypes):
            vs = self.get_denovo_variants(
                dnvStds, effectTypes=effectTypes, inChild=inChild)

            gnSorted = sorted([[ge['sym'], v]
                               for v in vs for ge in v.requestedGeneEffects])
            sym2Vars = {sym: [t[1] for t in tpi]
                        for sym, tpi in groupby(gnSorted, key=lambda x: x[0])}
            sym2FN = {sym: len(set([v.familyId for v in vs]))
                      for sym, vs in list(sym2Vars.items())}
            return {g for g, nf in list(sym2FN.items()) if nf > 1}, \
                {g for g, nf in list(sym2FN.items()) if nf == 1}

        addSet("prb.LoF",             genes('prb', 'LGDs'))
        recPrbLGDs, sinPrbLGDs = recSingleGenes('prb', 'LGDs')
        addSet("prb.LoF.Recurrent",   recPrbLGDs)
        addSet("prb.LoF.Single",      sinPrbLGDs)

        addSet("prb.LoF.Male",        genes('prbM', 'LGDs'))
        addSet("prb.LoF.Female",      genes('prbF', 'LGDs'))

        #         addSet("prb.LoF.LowIQ",       genes('prb', 'LGDs', maxIQ=90))
        #         addSet("prb.LoF.HighIQ",      genes('prb', 'LGDs', minIQ=90))

        addSet("prb.LoF.FMRP",        genes(
            'prb', 'LGDs', set_genes("main:FMR1-targets")))
        # addSet("prbLGDsInCHDs",
        # genes('prb','LGDs',
        # set("CHD1,CHD2,CHD3,CHD4,CHD5,CHD6,CHD7,CHD8,CHD9".split(','))))

        addSet("prb.Missense",        genes('prb', 'missense'))
        addSet("prb.Missense.Male",   genes('prbM', 'missense'))
        addSet("prb.Missense.Female", genes('prbF', 'missense'))
        addSet("prb.Synonymous",      genes('prb', 'synonymous'))

        addSet("sib.LoF",             genes('sib', 'LGDs'))
        addSet("sib.Missense",        genes('sib', 'missense'))
        addSet("sib.Synonymous",      genes('sib', 'synonymous'))

        '''
        addSet("A",      recPrbLGDs, "recPrbLGDs")
        addSet("B",      genes('prbF','LGDs'), "prbF")
        addSet("C",      genes('prb','LGDs',set_genes("main:FMR1-targets")),
               "prbFMRP")
        addSet("D",      genes('prb','LGDs',maxIQ=90),"prbML")
        addSet("E",      genes('prb','LGDs',minIQ=90),"prbMH")

        addSet("AB",     set(r.t2G['A']) | set(r.t2G['B']))
        addSet("ABC",    set(r.t2G['A']) | set(r.t2G['B'])  | set(r.t2G['C']))
        addSet("ABCD",   set(r.t2G['A']) | set(r.t2G['B'])  |
                            set(r.t2G['C'])  | set(r.t2G['D']) )
        addSet("ABCDE",   set(r.t2G['A']) | set(r.t2G['B'])  |
                            set(r.t2G['C'])  | set(r.t2G['D']) |
                            set(r.t2G['E']) )
        '''

        recPrbCNVs, _sinPrbCNVs = recSingleGenes('prb', 'CNVs')
        addSet("prb.CNV.Recurrent",     recPrbCNVs)

        addSet("prb.CNV",   genes('prb', 'CNVs'))
        addSet("prb.Dup",   genes('prb', 'CNV+'))
        addSet("prb.Del",   genes('prb', 'CNV-'))

        addSet("sib.CNV",   genes('sib', 'CNVs'))
        addSet("sib.Dup",   genes('sib', 'CNV+'))
        addSet("sib.Del",   genes('sib', 'CNV-'))

        return r

    # THE ONES BELOW SHOULD BE MOVED
    # return a list of valid variant types, add None to this list for the UI

    def effectTypesSet(self, effectTypesS):
        return get_effect_types_set(effectTypesS)
        '''
        if effectTypesS == "CNVs":
            return { "CNV+", "CNV-" }
        if effectTypesS == "LGDs":
            return { "frame-shift", "nonsense", "splice-site", "no-frame-shift-new-stop", "no-frame-shift-new-Stop" }
        if effectTypesS == "nonsynonymous":
            return { "frame-shift", "nonsense", "splice-site", "no-frame-shift-new-stop", "no-frame-shift-new-Stop",
                    "missense", "no-frame-shift" }
        return set(effectTypesS.split(","))
        '''


# added sep param in order to produce CSV outout for Web Site
def _safeVs(tf, vs, atts=[], sep="\t"):
    def ge2Str(gs):
        return "|".join(x['sym'] + ":" + x['eff'] for x in gs)

    mainAtts = "familyId studyName location variant bestSt fromParentS inChS counts geneEffect requestedGeneEffects popType".split()
    specialStrF = {"bestSt": mat2Str, "counts": mat2Str,
                   "geneEffect": ge2Str, "requestedGeneEffects": ge2Str}

    tf.write(sep.join(mainAtts + atts) + "\n")
    for v in vs:
        mavs = []
        for att in mainAtts:
            try:
                if att in specialStrF:
                    mavs.append(specialStrF[att](getattr(v, att)))
                else:
                    mavs.append(str(getattr(v, att)))
            except:
                mavs.append("")

        tmp = sep.join(
            mavs + [str(v.atts[a]).replace(sep, ';') if a in v.atts else "" for a in atts])
        tf.write(tmp + "\n")


def viewVs(vs, atts=[]):
    tf = tempfile.NamedTemporaryFile("w", delete=False)
    print("temp file name: {}".format(tf.name), file=sys.stderr)
    _safeVs(tf, vs, atts)
    tf.close()
    os.system("oocalc " + tf.name)
    os.remove(tf.name)


def safeVs(vs, fn, atts=[]):
    if fn == "-":
        f = sys.stdout
    else:
        f = open(fn, "w")
    _safeVs(f, vs, atts)
    if fn != "-":
        f.close()


if __name__ == "__main__":
    wd = os.environ['DAE_DB_DIR']
    print("wd: {}".format(wd))

    from Config import *
    config = Config()

    # giDB = GeneInfoDB(config.geneInfoDBconfFile, config.daeDir)
    # sfariDB = SfariCollection(config.sfariDBdir)
    # phDB = phenoDB.rawTableFactory(config.phenoDBFile)
    # genomesDB = GenomesDB(config.daeDir, config.genomesDBconfFile )

    vDB = VariantsDB(config.daeDir, config.variantsDBconfFile)

    st = vDB.get_study("IossifovWE2014")
    fd = st.families['13394']
    print(", ".join([fd.familyId, len(fd.memberInOrder), fd.atts]))
    for pd in fd.memberInOrder:
        print(", ".join(["\t", pd.personId, pd.role, pd.gender, pd.atts]))

    '''
    for v in vDB.get_validation_variants():
        # pass
        print v.familyId,v.location,v.variant,v.valStatus
    '''

    '''
    st = vDB.get_study('wig683')

    v = st.get_transmitted_variants().next()

    # st = vDB.get_study('LevyCNV2011')
    for v in st.get_denovo_variants():
        if v.inChS != v.atts['inChild']:
            print v.familyId, "".join([str(v.get_normal_refCN(c)) for c in xrange(v.bestSt.shape[1])]), "\t", mat2Str(v.bestSt), "    \t", v.inChS, v.atts['inChild'], v.location, v.variant, "   \t", [(p.role, p.gender) for p in v.study.families[v.familyId].memberInOrder]
    '''
    '''
    st = vDB.get_study('wig683')

    for v in st.get_transmitted_summary_variants(minParentsCalled=0,maxAltFreqPrcnt=-1, regionS="10:90000-94000"):
        print "SUMMARY:", v.location, v.variant

    for v in st.get_transmitted_variants(minParentsCalled=0,maxAltFreqPrcnt=-1, regionS="10:92990-92990"):
        print "FAMILY :", v.location, v.variant, v.familyId

    '''
    # rs = vDB.get_study('wigRNASeq')
    # viewVs(vDB.get_study('wig683').get_denovo_variants(effectTypes="LGDs"))

    # print "OOOOOOOOO", len(list(vDB.get_denovo_variants([vDB.get_study("DalyWE2012"), vDB.get_study("EichlerWE2012"), vDB.get_study("wig683")], effectTypes="LGDs", inChild="prb")))
    # sd = vDB.get_study("DalyWE2012")
    # sd = vDB.get_study("EichlerWE2012")
    # sd = vDB.get_study("StateWE2012")
    # sd = vDB.get_study("LevyCNV2011")
    # sd = vDB.get_study("wig683")

    # for tt in [(x.familyId, x.location, x.bestSt,x.atts['inChild']) for x in sd.get_denovo_variants(inChild="sib")]:
    #    print tt


'''
    fo = open("CHD5-nv.txt","w")
    fo.write("\t".join("mikesEncoding familyId location variant bestSt counts familyGenderType "
                     "fromParent inChildren popType altFreqPrcnt effectType effectGene effectDetails".split()) + "\n")

    for v in sd.get_transmitted_variants(maxAltFreqPrcnt=1.0,geneSyms={"CHD5"}):
        bs = v.bestSt
        mbrs = sd.families[v.familyId].memberInOrder

        parentStr = ''
        childStr = ''
        if bs[1][0]:
            parentStr += "mom"
        if bs[1][1]:
            parentStr += "dad"
        for c in xrange(2,len(mbrs)):
            if bs[1][c]:
                childStr += (mbrs[c].role + mbrs[2].gender)

        mikesEncoding = "[M%d F%d A%s%d S%s%d]" % (bs[1,0], bs[1,1], mbrs[2].gender, bs[1,2], mbrs[3].gender, bs[1,3])

        fo.write("\t".join((mikesEncoding, v.familyId, v.location, v.variant, v.bestStStr, v.countsStr,
            sd.families[v.familyId].memberInOrder[2].gender+sd.families[v.familyId].memberInOrder[3].gender,
            parentStr, childStr,
            v.popType, str(v.altFreqPrcnt), v.atts['effectType'], v.atts['effectGene'], v.atts['effectDetails'])) + "\n")
    fo.close()
'''

# vDB.getDenovoVariants('wigler582')
# vDB.getDenovoVariants('3papers')
#
# res = vDB.getDenovoVariantsGeneSyms('wig582-3pap',inChildRole='prb', effectTypes="LGDs")
# right = set()
# for l in open(wd + '/rightPrbLGDs.txt'):
#     right.add(l.strip())

# print len(res), len(right)
# print 'res but not right:', " ".join([g for g in res if not g in right])
# print 'right but not res:', " ".join([g for g in right if not g in res])

# print "\n".join(["\t".join((v.center, v.geneEffect[0]['sym'], v.majorEffect))
#                 for v in vDB.getDenovoVariants('wig582-3pap',effectTypes="LGDs")
#                 ])
