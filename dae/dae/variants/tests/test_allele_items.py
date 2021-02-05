"""
Created on Mar 20, 2018

@author: lubo
"""
import pytest

# from dae.variants.variant import AltAlleleItems


# def test_allele_items():
#     all_items = AltAlleleItems([1, 2, 3])

#     assert all_items[1] == 1
#     assert all_items[3] == 3

#     with pytest.raises(IndexError):
#         all_items[4]

#     items = all_items[2:]
#     assert len(items) == 2
#     assert items == [2, 3]

#     items = all_items[1:]
#     assert len(items) == 3
#     assert items == [1, 2, 3]

#     items = all_items[:-1]
#     assert len(items) == 2
#     assert items == [1, 2]

#     items = all_items[:]
#     assert len(items) == 3
#     assert items == [1, 2, 3]


# def test_allele_negative_index():
#     all_items = AltAlleleItems([1, 2, 3])

#     assert all_items[-1] == 3
#     assert all_items[-3] == 1

#     with pytest.raises(IndexError):
#         all_items[-4]

#     with pytest.raises(IndexError):
#         all_items[0]


# def test_allele_items_slices_positive_step():
#     all_items = AltAlleleItems([1, 2, 3, 4])

#     items = all_items[::1]
#     assert len(items) == 4
#     assert items == [1, 2, 3, 4]

#     items = all_items[::2]
#     assert len(items) == 2
#     assert items == [1, 3]

#     items = all_items[::3]
#     assert len(items) == 2
#     assert items == [1, 4]

#     items = all_items[::1000]
#     assert len(items) == 1
#     assert items == [1]

#     items = all_items[2::2]
#     assert len(items) == 2
#     assert items == [2, 4]


# def test_allele_items_slices_negative_step():
#     all_items = AltAlleleItems([1, 2, 3, 4])

#     items = all_items[::-1]
#     assert len(items) == 4
#     assert items == [4, 3, 2, 1]

#     items = all_items[:-5:-1]
#     assert len(items) == 4
#     assert items == [4, 3, 2, 1]


# def test_allele_items_iter():
#     all_items = AltAlleleItems([1, 2, 3, 4])

#     items = [i for i in all_items]
#     assert [1, 2, 3, 4] == items

#     it = iter(all_items)
#     item = next(it)
#     assert item == 1

#     item = next(it)
#     assert item == 2


# def test_allele_items_join():
#     all_items = AltAlleleItems(["A", "B"])
#     assert "A,B" == ",".join(all_items)
