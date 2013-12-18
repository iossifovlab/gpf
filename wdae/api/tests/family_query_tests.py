import unittest
import itertools

#from DAE import vDB
from query_variants import dae_query_variants, get_parents_race, get_verbal_iq

# class FamilyRaceTests(unittest.TestCase):

#     def test_asian_race(self):
#         query_string = {'denovoStudies': 'allWEAndTG',
#                         'familyRace': 'asian'}
#         vsl = dae_query_variants(query_string)
#         par_race = get_parents_race()

#         for v in itertools.chain(*vsl):
#             self.assertEquals('asian', par_race[v.familyId])

#     def test_african_amer_race(self):
#         query_string = {'denovoStudies': 'allWEAndTG',
#                         #'transmittedStudies': 'w873e374s322',
#                         'familyRace': 'african-amer'}

#         vsl = dae_query_variants(query_string)
#         par_race = get_parents_race()

#         for v in itertools.chain(*vsl):
#             self.assertEquals('african-amer', par_race[v.familyId])


# class FamilyVerbalIqTest(unittest.TestCase):

#     def test_max_verbal_iq(self):
#         query_string = {'denovoStudies': 'allWEAndTG',
#                         'familyVerbalIqHi': '50.0'}
#         vsl = dae_query_variants(query_string)
#         verb_iq = get_verbal_iq()

#         for v in itertools.chain(*vsl):
#             self.assertTrue(verb_iq[v.familyId] <= 50.0)

#     def test_min_verbal_iq(self):
#         query_string = {'denovoStudies': 'allWEAndTG',
#                         'familyVerbalIqLo': '50.0'}
#         vsl = dae_query_variants(query_string)
#         verb_iq = get_verbal_iq()

#         for v in itertools.chain(*vsl):
#             self.assertTrue(verb_iq[v.familyId] >= 50.0)

#     def test_min_max_verbal_iq(self):
#         query_string = {'denovoStudies': 'allWEAndTG',
#                         'familyVerbalIqLo': '50.0',
#                         'familyVerbalIqHi': '90.0'}

#         vsl = dae_query_variants(query_string)
#         verb_iq = get_verbal_iq()

#         for v in itertools.chain(*vsl):
#             self.assertTrue(verb_iq[v.familyId] >= 50.0)
#             self.assertTrue(verb_iq[v.familyId] <= 90.0)


# # class FamilyPrbSibGenderTest(unittest.TestCase):

# #     def test_prb_male(self):
# #         query_string = {'denovoStudies': 'allWEAndTG',
# #                         'familyPrbGender': 'male'}
# #         vsl = dae_query_variants(query_string)
# #         prb_gender = get_prb_gender()

# #         count = 0
# #         for v in itertools.chain(*vsl):
# #             count += 1
# #             self.assertEquals('male', prb_gender[v.familyId])

# #         self.assertTrue(count >= 0)

# #     def test_prb_female(self):
# #         query_string = {'denovoStudies': 'allWEAndTG',
# #                         'familyPrbGender': 'FeMale'}
# #         vsl = dae_query_variants(query_string)
# #         prb_gender = get_prb_gender()

# #         count = 0
# #         for v in itertools.chain(*vsl):
# #             count += 1
# #             self.assertEquals('female', prb_gender[v.familyId])

# #         self.assertTrue(count >= 0)

# #     def test_sib_male(self):
# #         query_string = {'denovoStudies': 'allWEAndTG',
# #                         'familySibGender': 'male'}
# #         vsl = dae_query_variants(query_string)
# #         sib_gender = get_sib_gender()

# #         count = 0
# #         for v in itertools.chain(*vsl):
# #             count += 1
# #             self.assertEquals('male', sib_gender[v.familyId])

# #         self.assertTrue(count >= 0)

# #     def test_sib_female(self):
# #         query_string = {'denovoStudies': 'allWEAndTG',
# #                         'familySibGender': 'FeMale'}
# #         vsl = dae_query_variants(query_string)
# #         sib_gender = get_sib_gender()

# #         count = 0
# #         for v in itertools.chain(*vsl):
# #             count += 1
# #             self.assertEquals('female', sib_gender[v.familyId])

# #         self.assertTrue(count >= 0)


# from api.family_query import filter_variants_quad, filter_variants_trio


# class FamilyQuadTrio(unittest.TestCase):

#     def test_quad(self):
#         query_string = {'denovoStudies': 'allWEAndTG'}

#         vsl = dae_query_variants(query_string)
#         count = 0
#         for v in itertools.ifilter(filter_variants_quad,
#                                    itertools.chain(*vsl)):
#             self.assertEquals(4, len(v.memberInOrder))
#             count += 1

#         self.assertTrue(count > 0)

#     def test_trio(self):
#         query_string = {'denovoStudies': 'allWEAndTG'}

#         vsl = dae_query_variants(query_string)
#         count = 0
#         for v in itertools.ifilter(filter_variants_trio,
#                                    itertools.chain(*vsl)):
#             self.assertEquals(3, len(v.memberInOrder))
#             count += 1

#         self.assertTrue(count > 0)


# from api.family_query import filter_proband_male, filter_proband_female, \
#     filter_sibling_male, filter_sibling_female


# class FamilyPrbGenderPost(unittest.TestCase):
#     def test_prb_male(self):
#         query_string = {'denovoStudies': 'allWEAndTG'}

#         vsl = dae_query_variants(query_string)
#         count = 0
#         for v in itertools.ifilter(filter_proband_male,
#                                    itertools.chain(*vsl)):
#             self.assertEquals('M', v.memberInOrder[2].gender)
#             count += 1

#         self.assertTrue(count > 0)

#     def test_prb_female(self):
#         query_string = {'denovoStudies': 'allWEAndTG'}

#         vsl = dae_query_variants(query_string)
#         count = 0
#         for v in itertools.ifilter(filter_proband_female,
#                                    itertools.chain(*vsl)):
#             self.assertEquals('F', v.memberInOrder[2].gender)
#             count += 1

#         self.assertTrue(count > 0)


# class FamilySibGenderPost(unittest.TestCase):
#     def test_sib_male(self):
#         query_string = {'denovoStudies': 'allWEAndTG'}

#         vsl = dae_query_variants(query_string)
#         count = 0
#         for v in itertools.ifilter(filter_sibling_male,
#                                    itertools.chain(*vsl)):
#             self.assertEquals('M', v.memberInOrder[3].gender)
#             count += 1

#         self.assertTrue(count > 0)

#     def test_sib_female(self):
#         query_string = {'denovoStudies': 'allWEAndTG'}

#         vsl = dae_query_variants(query_string)
#         count = 0
#         for v in itertools.ifilter(filter_sibling_female,
#                                    itertools.chain(*vsl)):
#             self.assertEquals('F', v.memberInOrder[3].gender)
#             count += 1

#         self.assertTrue(count > 0)


# # class CombineFiltersPost(unittest.TestCase):
# #     def test_prb_male_sib_male(self):
# #         query_string = {'denovoStudies': 'allWEAndTG'}

# #         vsl = dae_query_variants(query_string)
# #         count = 0
# #         cf = combine_filters([filter_proband_male, filter_sibling_male])

# #         for v in itertools.ifilter(cf, itertools.chain(*vsl)):
# #             self.assertEquals('M', v.memberInOrder[2].gender)
# #             self.assertEquals('M', v.memberInOrder[3].gender)
# #             count += 1

# #         self.assertTrue(count > 0)

# #     def test_prb_male_sib_female(self):
# #         query_string = {'denovoStudies': 'allWEAndTG'}

# #         vsl = dae_query_variants(query_string)
# #         count = 0
# #         cf = combine_filters([filter_proband_male, filter_sibling_female])

# #         for v in itertools.ifilter(cf, itertools.chain(*vsl)):
# #             self.assertEquals('M', v.memberInOrder[2].gender)
# #             self.assertEquals('F', v.memberInOrder[3].gender)
# #             count += 1

# #         self.assertTrue(count > 0)
