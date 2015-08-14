'''
Created on Aug 13, 2015

@author: lubo
'''
import tables
from api.variants.hdf5_builder import FamilyVariants, SummaryVariants
from DAE import vDB
import numpy as np


class GeneNameIndex(tables.IsDescription):
    gene_name = tables.StringCol(28)
    chrome = tables.StringCol(4)


class TransmissionQueryReindex(object):
    filters = tables.Filters(complevel=0)

    def __init__(self, study_name):
        self.study_name = study_name
        self.study = vDB.get_study(self.study_name)
        # self.hdf5_filename = vDB._config.get(
        #             'study.' + self.study_name,
        #             'transmittedVariants.hdf5')
        self.hdf5_filename = '{}.hdf5'.format(study_name)
        self.hdf5_fh = tables.open_file(self.hdf5_filename, "r+",
                                        filters=self.filters)

    def create_family_index(self):
        ftable = self.hdf5_fh.root.variants.family
        assert ftable
        ftable.cols.family_id.reindex()
        ftable.reindex()

    def create_gene_index(self):
        etable = self.hdf5_fh.root.variants.effect
        assert etable
        etable.cols.gene_sym.reindex()
        etable.reindex()

    def check_all_family_variants(self):
        ftable = self.hdf5_fh.root.variants.family
        frows = ftable.read_where('family_id == "13785"')
        return frows

    def build_index_for_family_variants(self):
        if 'families' not in self.hdf5_fh.root:
            fgroup = self.hdf5_fh.create_group('/', 'families',
                                               'Families Index')
        else:
            fgroup = self.hdf5_fh.root.families
        for family_id in self.study.families.keys():
            print "building index for ", family_id
            self.build_single_family_index(fgroup, family_id)

    def build_single_family_index(self, fgroup, family_id):
        fname = 'f{}'.format(family_id)
        if fname in fgroup:
            findex = fgroup._f_get_child(fname)
            findex._f_remove()

        ftable = self.hdf5_fh.root.variants.family
        frows = ftable.read_where('family_id == "{}"'.format(family_id))
        findex = self.hdf5_fh.create_table(fgroup, fname,
                                           FamilyVariants, 'Family Index')
        findex.append(frows)
        findex.flush()

    chromes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
               '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
               '21', '22', 'X']

    def build_index_for_chromes(self):
        if 'chromes' not in self.hdf5_fh.root:
            chgroup = self.hdf5_fh.create_group('/', 'chromes',
                                                'chromes index')
        else:
            chgroup = self.hdf5_fh.root.chromes

        stable = self.hdf5_fh.root.variants.summary

        for chrome in self.chromes:
            print "building index for chrome ", chrome
            chname = "ch{}".format(chrome)
            if chname in chgroup:
                chindex = chgroup._f_get_child(chname)
                chindex._f_remove()

            chindex = self.hdf5_fh.create_table(
                chgroup, chname,
                SummaryVariants, 'Chrome {} Index'.format(chrome))

            srows = stable.read_where('chrome == "{}"'.format(chrome))
            chindex.append(srows)
            chindex.flush()

    def build_index_for_gene_names(self, ggroup):
        if 'gene_names' in ggroup:
            gnindex = ggroup.gene_names
            gnindex._f_remove()
        gm = self.study.vdb.genomesDB.get_gene_models()
        gene_names = gm.gene_names()
        genes = []
        for sym in gene_names:
            g = gm.gene_models_by_gene_name(sym)[0]
            genes.append((g.chr, sym))
        genes = np.array(genes, dtype=[('chrome', 'S4'), ('gene_name', 'S28')])
        gnindex = self.hdf5_fh.create_table(
            ggroup, 'gene_names',
            GeneNameIndex, 'Gene Names Index')
        gnindex.append(genes)
        gnindex.flush()

    def build_index_for_gene_variants(self, ggroup):
        if 'gene_variants' in ggroup:
            gvgroup = ggroup.gene_variants
        else:
            gvgroup = self.hdf5_fh.create_group(ggroup, 'gene_variants',
                                                'gene variants indexes')
        gene_names = ggroup.gene_names[:]['gene_name']
        print gene_names
        for gene_sym in gene_names:
            print 'building gene index for ', gene_sym
            self.build_index_for_gene_symbol(gvgroup, gene_sym)

    def build_index_for_gene_symbol(self, gvgroup, gene_sym):
        gindex_name = 'g{}'.format(gene_sym)
        if gindex_name in gvgroup:
            gvindex = gvgroup._f_get_child(gindex_name)
            gvindex._f_remove()
        gvindex = self.hdf5_fh.create_table(
            gvgroup, gindex_name,
            SummaryVariants, 'Gene {} Variants Index'.format(gene_sym))
        etable = self.hdf5_fh.root.variants.effect
        stable = self.hdf5_fh.root.variants.summary
        where = 'symbol == "{}"'.format(gene_sym)
        print where
        erows = etable.read_where(where)
        vrows = stable[erows['vrow']][:]
        vrows['effect_type'] = erows['effect_type']
        vrows['effect_gene'] = gene_sym
        gvindex.append(vrows)
        gvindex.flush()

    def build_index_for_genes(self):
        if 'genes' not in self.hdf5_fh.root:
            ggroup = self.hdf5_fh.create_group('/', 'genes',
                                               'genes index')
        else:
            ggroup = self.hdf5_fh.root.genes
        self.build_index_for_gene_names(ggroup)
        self.build_index_for_gene_variants(ggroup)


if __name__ == "__main__":
    tqr = TransmissionQueryReindex('w1202s766e611')
    # tqr.build_index_for_family_variants()
    # tqr.build_index_for_chromes()
    tqr.build_index_for_genes()
