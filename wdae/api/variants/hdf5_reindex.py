'''
Created on Aug 13, 2015

@author: lubo
'''
import tables


class FamilyIndex(tables.IsDescription):
    family_id = tables.StringCol(16)
    index = tables.Int64Col()
    # vrow = tables.Int64Col()


class TransmissionQueryReindex(object):
    filters = tables.Filters(complevel=0)

    def __init__(self, study_name):
        self.study_name = study_name
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

    def build_index_family_row(self, family_id, index):
        if 'families' not in self.hdf5_fh.root:
            fgroup = self.hdf5_fh.create_group('/', 'families',
                                               'Families Index')
        else:
            fgroup = self.hdf5_fh.root.families

        fid = "i{}".format(family_id)
        if fid not in fgroup:
            print "create family index table"
            findex = self.hdf5_fh.create_table(fgroup, fid,
                                               FamilyIndex, 'Family Index')
        else:
            findex = self.hdf5_fh.root.families._f_get_child(fid)
        row = findex.row
        row['family_id'] = family_id
        row['index'] = index
        row.append()
        # findex.flush()

    def build_index_for_family_variants(self):
        ftable = self.hdf5_fh.root.variants.family
        for (n, frow) in enumerate(ftable):
            family_id = frow['family_id']
            self.build_index_family_row(family_id, n)
            if n % 10000 == 0:
                print "index", n

        for f in self.hdf5_fh.root.families:
            f.flush()


if __name__ == "__main__":
    tqr = TransmissionQueryReindex('w1202s766e611')
    tqr.build_index_for_family_variants()
