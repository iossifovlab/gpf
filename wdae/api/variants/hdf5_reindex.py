'''
Created on Aug 13, 2015

@author: lubo
'''
import tables
from api.variants.hdf5_builder import FamilyVariants
from DAE import vDB


class FamilyIndex(tables.IsDescription):
    family_id = tables.StringCol(16)
    index = tables.Int64Col()
    # vrow = tables.Int64Col()


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


if __name__ == "__main__":
    tqr = TransmissionQueryReindex('w1202s766e611')
    tqr.build_index_for_family_variants()
