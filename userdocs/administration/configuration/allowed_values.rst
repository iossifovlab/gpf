Allowed Configuration Values
============================

This is a reference list of allowed values for various
configuration variables and attributes.


.. _allowed_values_booleans:

Booleans
--------

* ``yes``
* ``Yes``
* ``true``
* ``True``
* ``no``
* ``No``
* ``false``
* ``False``

.. _allowed_values_gene_effect_types:

Gene effect types
-----------------

* ``3'UTR``
* ``3'UTR-intron``
* ``5'UTR``
* ``5'UTR-intron``
* ``frame-shift``
* ``intergenic``
* ``intron``
* ``missense``
* ``no-frame-shift``
* ``no-frame-shift-newStop``
* ``noEnd``
* ``noStart``
* ``non-coding``
* ``non-coding-intron``
* ``nonsense``
* ``splice-site``
* ``synonymous``
* ``CDS``
* ``CNV+``
* ``CNV-``

.. _allowed_values_gene_effect_groups:

Gene effect groups
------------------

This lists the valid gene effect groups and which effect types they encompass.

* Coding
    * ``Nonsense``
    * ``Frame-shift``
    * ``Splice-site``
    * ``No-frame-shift-newStop``
    * ``Missense``
    * ``No-frame-shift``
    * ``noStart``
    * ``noEnd``
    * ``Synonymous``

* Noncoding
    * ``Non coding``
    * ``Intron``
    * ``Intergenic``
    * ``3'-UTR``
    * ``5'-UTR``

* CNV
    * ``CNV+``
    * ``CNV``

* LGDs
    * ``Frame-shift``
    * ``Nonsense``
    * ``Splice-site``
    * ``No-frame-shift-newStop``

* Nonsynonymous
    * ``Nonsense``
    * ``Frame-shift``
    * ``Splice-site``
    * ``No-frame-shift-newStop``
    * ``Missense``
    * ``No-frame-shift``
    * ``noStart``
    * ``noEnd``

* UTRs
    * ``3'-UTR``
    * ``5'-UTR``


.. _allowed_values_sex:

Sex
---

* ``0`` or ``U`` or ``unspecified``
* ``1`` or ``M`` or ``male``
* ``2`` or ``F`` or ``female``


.. _allowed_values_inheritance:

Inheritance
-----------

* ``reference``
* ``mendelian``
* ``denovo``
* ``possible_denovo``
* ``omission``
* ``other``
* ``missing``
* ``unknown``


.. _allowed_values_role:

Role
----

* ``maternal_grandmother``
* ``maternal_grandfather``
* ``paternal_grandmother``
* ``paternal_grandfather``
* ``mom``
* ``dad``
* ``parent``
* ``prb``
* ``sib``
* ``child``
* ``maternal_half_sibling``
* ``paternal_half_sibling``
* ``half_sibling``
* ``maternal_aunt``
* ``maternal_uncle``
* ``paternal_aunt``
* ``paternal_uncle``
* ``maternal_cousin``
* ``paternal_cousin``
* ``step_mom``
* ``step_dad``
* ``spouse``
* ``unknown``


.. _allowed_values_status:

Status
------

Unspecified values indicate unknown status.

* ``0``: unknown
* ``1``: unaffected
* ``2``: affected


.. _allowed_values_variant_type:

VariantType
-----------

* ``sub`` or ``substitution``
* ``ins`` or ``insertion``
* ``del`` or ``deletion``
* ``complex``
* ``CNV``
