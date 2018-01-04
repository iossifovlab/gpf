# Problems with VIP phenotype data

Some roles are ambiguous: Uncle, Cousin, Half sibling - maternal or paternal?
Even if that was known, e.g. paternal half sibling, these roles do not specify
a unique location for the person in the pedigree tree (no information about the
mom of this half sibling, may not have data for her).


## svip_phase_2_subjects.csv

### Very incomplete families

The family 15083 has only a grandmother.

```
sfari_id	cohort	sex	relationship_to_iip	genetic_status	genetic_status_source	inheritance_status	inheritance_status_source	race	race_source	reported_asd	included_in_svip_phase_1_dataset	has_potential_confound	age_at_evaluation	phase_1_clinical_assessment	phase_2_clinical_assessment
15083-x1	16p11.2	female	Grandmother	Negative (normal)	confirmed	na	na			0	0	0	811	0	0
```

### Families 15052 15319 15334 15312 15142 15144 have multiple probands
These families are completely skipped - no pedigree is built for them

```
skipping 15052; reason: 15052: 2 probands - [Individual(15052-x1), Individual(15052-x4)]
skipping 15319; reason: 15319: 3 probands - [Individual(15319-x1), Individual(15319-x2), Individual(15319-x4)]
skipping 15334; reason: 15334: 3 probands - [Individual(15334-x1), Individual(15334-x3), Individual(15334-x4)]
skipping 15312; reason: 15312: 3 probands - [Individual(15312-x1), Individual(15312-x4), Individual(15312-x5)]
skipping 15142; reason: 15142: 2 probands - [Individual(15142-x1), Individual(15142-x2)]
skipping 15144; reason: 15144: 2 probands - [Individual(15144-x1), Individual(15144-x4)]
```

### Family 14725 has two moms
It is also skipped

```
skipping 14725; reason: 14725: 2 moms - [Individual(14725-x49), Individual(14725-x55)]
```

### Family 15132 has an ambiguous role: maternal_half_sibling

```
family 15132 (person 15132-x2) with ambiguous role: Role.maternal_half_sibling
```


## svip_subjects.csv

### Many families with ambiguous roles

```
family 14913 (person 14913.x5) with ambiguous role: Role.maternal_half_sibling
family 14773 (person 14773.x39) with ambiguous role: Role.maternal_half_sibling
family 14910 (person 14910.x15) with ambiguous role: Role.maternal_half_sibling
family 14758 (person 14758.x4) with ambiguous role: Role.maternal_half_sibling
family 14757 (person 14757.x13) with ambiguous role: Role.maternal_half_sibling
family 14757 (person 14757.x21) with ambiguous role: Role.maternal_cousin
family 14757 (person 14757.x22) with ambiguous role: Role.maternal_cousin
family 14757 (person 14757.x23) with ambiguous role: Role.maternal_cousin
family 14757 (person 14757.x24) with ambiguous role: Role.maternal_cousin
family 14757 (person 14757.x8) with ambiguous role: Role.maternal_cousin
family 14929 (person 14929.x33) with ambiguous role: Role.maternal_half_sibling
family 14725 (person 14725.x45) with ambiguous role: Role.maternal_cousin
family 14725 (person 14725.x46) with ambiguous role: Role.maternal_cousin
family 14725 (person 14725.x50) with ambiguous role: Role.maternal_half_sibling
family 14725 (person 14725.x51) with ambiguous role: Role.maternal_half_sibling
family 14725 (person 14725.x53) with ambiguous role: Role.maternal_half_sibling
family 14725 (person 14725.x54) with ambiguous role: Role.maternal_half_sibling
family 14739 (person 14739.x4) with ambiguous role: Role.maternal_half_sibling
family 14736 (person 14736.x10) with ambiguous role: Role.maternal_half_sibling
family 14780 (person 14780.x5) with ambiguous role: Role.maternal_half_sibling
family 14780 (person 14780.x6) with ambiguous role: Role.maternal_half_sibling
family 14704 (person 14704.x8) with ambiguous role: Role.maternal_half_sibling
family 14818 (person 14818.x17) with ambiguous role: Role.maternal_half_sibling
family 14818 (person 14818.x18) with ambiguous role: Role.maternal_half_sibling
family 14872 (person 14872.x42) with ambiguous role: Role.maternal_cousin
family 14791 (person 14791.x28) with ambiguous role: Role.maternal_half_sibling
family 14970 (person 14970.x11) with ambiguous role: Role.maternal_half_sibling
family 14970 (person 14970.x9) with ambiguous role: Role.maternal_half_sibling
family 14715 (person 14715.x39) with ambiguous role: Role.maternal_half_sibling
family 14715 (person 14715.x40) with ambiguous role: Role.maternal_half_sibling
family 14788 (person 14788.x34) with ambiguous role: Role.maternal_half_sibling
family 14788 (person 14788.x35) with ambiguous role: Role.maternal_half_sibling
family 14767 (person 14767.x29) with ambiguous role: Role.maternal_cousin
family 14763 (person 14763.x8) with ambiguous role: Role.maternal_half_sibling
family 14769 (person 14769.x12) with ambiguous role: Role.maternal_half_sibling
family 14769 (person 14769.x13) with ambiguous role: Role.maternal_half_sibling
family 14769 (person 14769.x14) with ambiguous role: Role.maternal_half_sibling
```

### Families with multiple probands from svip_phase_2_subjects.csv are missing here

```
15052, 15319, 15334, 15312, 15142, 15144
```

### Family 14725 (with two moms) from svip_phase_2_subjects.csv is correct in here

```
sfari_id	family	mother	father	family_type	collection	age_months	sex	relationship_to_iip	genetic_status_16p	inheritance_information
14725.x26	14725	14725.x18	14725.x17	16p-duplication	svip-16p	668	female	Grandmother	negative	na
14725.x39	14725	14725.x26	14725.x25	16p-duplication	svip-16p	420	male	Uncle	duplication	unknown
14725.x45	14725	14725.x6	14725.x39	16p-duplication	svip-16p	87	male	Cousin	negative	na
14725.x46	14725	14725.x55	14725.x39	16p-duplication	svip-16p	120	female	Cousin	duplication	inherited
14725.x48	14725	14725.x26	14725.x25	16p-duplication	svip-16p	415	male	Father	duplication	unknown
14725.x49	14725	14725.x28	14725.x27	16p-duplication	svip-16p	335	female	Mother	negative	na
14725.x50	14725	14725.x60	14725.x48	16p-duplication	svip-16p	97	female	Half sibling	negative	na
14725.x51	14725	14725.x60	14725.x48	16p-duplication	svip-16p	134	male	Half sibling	duplication	inherited
14725.x52	14725	14725.x49	14725.x48	16p-duplication	svip-16p	17	male	Initially identified proband	duplication	inherited
14725.x53	14725	14725.x49	14725.x13	16p-duplication	svip-16p	108	female	Half sibling	negative	na
14725.x54	14725	14725.x49	14725.x14	16p-duplication	svip-16p	57	male	Half sibling	negative	na
14725.x55	14725	14725.x57	14725.x56	16p-duplication	svip-16p	415	female		negative	na
14725.x60	14725	14725.x59	14725.x58	16p-duplication	svip-16p	359	female		negative	na

```

One of the two mothers (`14725.x55`) here has no role.

Also `14725.x60` has no role.

Both of those have a mother and father (`14725.x57`	`14725.x56` and
`14725.x59`	`14725.x58` respectively) as ids which are not present in the csv file.
