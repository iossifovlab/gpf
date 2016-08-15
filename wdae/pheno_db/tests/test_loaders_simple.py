'''
Created on Aug 10, 2016

@author: lubo
'''
import unittest
from pheno_db.utils.load_raw import V14Loader
# import collections
# import pprint


class V14LoaderTest(unittest.TestCase):

    def setUp(self):
        self.loader = V14Loader()

    def tearDown(self):
        pass

    def test_config(self):
        self.assertIsNotNone(self.loader.v14)
        self.assertIsNotNone(self.loader.v15)

    def test_v14_load_main(self):
        df = self.loader.load_main()
        self.assertIsNotNone(df)

    def test_v14_load_cdv(self):
        df = self.loader.load_cdv()
        self.assertIsNotNone(df)

    def test_check_cdv_categories(self):
        df = self.loader.load_cdv()
        df1 = self.loader._load_df(self.loader.CDV_OLD)

        self.assertIsNotNone(df1)
        self.assertEquals(len(df1), len(df))
        self.assertTrue((df.variableCategory == df1.variableCategory).all())

    def test_v14_load_ocuv(self):
        df = self.loader.load_ocuv()
        self.assertIsNotNone(df)

    def test_load_everything(self):
        df = self.loader.load_everything()
        self.assertIsNotNone(df)

    def test_compare_columns_in_cdv_and_ocuv(self):
        cdv = self.loader.load_cdv()
        ocuv = self.loader.load_ocuv()

        print(cdv.columns)
        print(ocuv.columns)

        self.assertTrue((cdv.columns == ocuv.columns).all())

    def test_check_ocuv_categories(self):
        df = self.loader.load_ocuv()
        df1 = self.loader._load_df(self.loader.OCUV_OLD)

        self.assertIsNotNone(df1)
        self.assertEquals(len(df1), len(df))
        self.assertTrue((df.variableCategory == df1.variableCategory).all())

#     def test_check_cdv_measures_in_everything(self):
#         cdv = self.loader.load_cdv()
#         df = self.loader.load_everything()
#
#         print(cdv.columns)
#
#         print(len(df.columns))
#         print(df.columns)
#         print(len(df.columns))
#
#         for _index, md in cdv.iterrows():
#             found = False
#             for col in df.columns:
#                 if md['variableId'] in col:
#                     print("col: {}; tableName: {}, name: {}; columnId: {}"
#                           .format(
#                               col,
#                               md['tableName'],
#                               md['name'],
#                               md['variableId']))
#                     found = True
#             if not found:
#                 print("NOT FOUND: tableName: {}, name: {}; columnId: {}"
#                       .format(
#                           md['tableName'],
#                           md['name'],
#                           md['variableId']))
#
#     def test_match_cdv_to_main(self):
#         cdv = self.loader.load_cdv()
#         main = self.loader.load_main()
#
#         for _cdvindex, md in cdv.iterrows():
#             found = False
#             for _mainindex, mmd in main.iterrows():
#                 if mmd['variableId'] in md['columnId']:
#                     found = True
#                     print("cdv columnId: {} = main uniqueVariableId: {}"
#                           .format(
#                               md['columnId'], mmd['uniqueVariableId']
#                           ))
#             if not found:
#                 print("cdv columnId: {} not found"
#                       .format(
#                           md['columnId']
#                       ))
#
#     def test_check_main_measures_in_everything(self):
#         main = self.loader.load_main()
#         df = self.loader.load_everything()
#
#         found_count = 0
#         not_found_count = 0
#         not_found_list = []
#
#         tables_match = collections.defaultdict(set)
#
#         for _index, md in main.iterrows():
#             found = []
#             variable_name = md['variableId']
#             table_name = md['tableName']
#
#             for col_name in df.columns:
#                 if variable_name == col_name[-len(variable_name):]:
#                     #                     print("col: {}; main name: {}"
#                     #                           .format(
#                     #                               col,
#                     #                               main_name,
#                     #                           ))
#                     found.append(col_name)
#                     tables_match[table_name].add(col_name.split('.')[0])
#
#             if found:
#                 found_count += 1
# #                 if len(found) > 1:
# #                     print("table: {}; var: {}; found: {}"
# #                           .format(
# #                               table_name,
# #                               variable_name,
# #                               found
# #                           ))
#             else:
#                 not_found_count += 1
#                 not_found_list.append(md)
# #                 print("NOT FOUND: main name: {}"
# #                       .format(
# #                           main_name,
# #                       ))
#
#         pprint.pprint(tables_match)
#         print("tables: {}".format(len(tables_match)))
#         print("found: {}; not found: {}".format(
#            found_count, not_found_count))
#         # print("not found list: {}".format(not_found_list))

if __name__ == "__main__":
    unittest.main()
