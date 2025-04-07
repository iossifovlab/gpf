import { UserGroup } from 'app/users-groups/users-groups';
import {
  Column,
  ColumnGroup,
  Dataset,
  GeneBrowser,
  GenotypeBrowser,
  PersonFilter,
  PersonSetCollection,
  PersonSetCollections,
  PersonSet
} from './datasets';

describe('PersonSet', () => {
  const personSetJsons = [
    {
      id: 'id1',
      name: 'name1',
      color: 'color1'
    },
    {
      id: 'id2',
      name: 'name2',
      color: 'color2'
    }
  ];
  const personSetParams = [
    ['id1', 'name1', 'color1'],
    ['id2', 'name2', 'color2']
  ] as const;

  it('should create person set from json', () => {
    const mockPerson = PersonSet.fromJson(personSetJsons[0]);
    expect(new PersonSet(...personSetParams[0])).toStrictEqual(mockPerson);
  });

  it('should create person from array of json', () => {
    const mockPerson = PersonSet.fromJsonArray(personSetJsons);
    expect([
      new PersonSet(...personSetParams[0]),
      new PersonSet(...personSetParams[1])
    ]).toStrictEqual(mockPerson);
  });
});

describe('PersonSetCollection', () => {
  it('should create person set collection from json array', () => {
    const mockPersonSetCollection1 = [
      new PersonSetCollection(
        'id1',
        'name1',
        [
          new PersonSet('id1', 'name1', 'color1'),
          new PersonSet('id1', 'name2', 'color3'),
          new PersonSet('id2', 'name3', 'color4')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name2',
        [
          new PersonSet('id2', 'name2', 'color2'),
          new PersonSet('id2', 'name3', 'color5'),
          new PersonSet('id3', 'name4', 'color6')
        ]
      )
    ];

    const mockPersonSetCollection2 = PersonSetCollection.fromJson({
      id1: {
        id: 'id1',
        name: 'name1',
        domain: [
          {
            id: 'id1',
            name: 'name1',
            color: 'color1'
          },
          {
            id: 'id1',
            name: 'name2',
            color: 'color3'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color4'
          }
        ]
      },
      id2: {
        id: 'id2',
        name: 'name2',
        domain: [
          {
            id: 'id2',
            name: 'name2',
            color: 'color2'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color5'
          },
          {
            id: 'id3',
            name: 'name4',
            color: 'color6'
          }
        ]
      }
    });

    expect(mockPersonSetCollection1).toStrictEqual(mockPersonSetCollection2);
  });
});

describe('PersonSetCollections', () => {
  it('should create person set collections from json', () => {
    const mockPersonSetCollections1 = new PersonSetCollections([
      new PersonSetCollection(
        'id1',
        'name1',
        [
          new PersonSet('id1', 'name1', 'color1'),
          new PersonSet('id1', 'name2', 'color3'),
          new PersonSet('id2', 'name3', 'color4')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name2',
        [
          new PersonSet('id2', 'name2', 'color2'),
          new PersonSet('id2', 'name3', 'color5'),
          new PersonSet('id3', 'name4', 'color6')
        ]
      )
    ]);

    const mockPersonSetCollections2 = PersonSetCollections.fromJson({
      id1: {
        name: 'name1',
        domain: [
          {
            id: 'id1',
            name: 'name1',
            color: 'color1'
          },
          {
            id: 'id1',
            name: 'name2',
            color: 'color3'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color4'
          }
        ]
      },
      id2: {
        name: 'name2',
        domain: [
          {
            id: 'id2',
            name: 'name2',
            color: 'color2'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color5'
          },
          {
            id: 'id3',
            name: 'name4',
            color: 'color6'
          }
        ]
      }
    });

    expect(mockPersonSetCollections1).toStrictEqual(mockPersonSetCollections2);
  });

  it('should get legend from person set collection', () => {
    const mockPersonSetCollections1 = new PersonSetCollections([
      new PersonSetCollection(
        'id1',
        'name1',
        [
          new PersonSet('id1', 'name2', 'color3'),
          new PersonSet('id2', 'name3', 'color4'),
          new PersonSet('id1', 'name1', 'color1')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name2',
        [
          new PersonSet('id2', 'name2', 'color2'),
          new PersonSet('id2', 'name3', 'color5'),
          new PersonSet('id3', 'name4', 'color6')
        ]
      )
    ]);

    const mockPersonSetCollections2 = [];
    mockPersonSetCollections2.push(new PersonSet('id1', 'name2', 'color3'));
    mockPersonSetCollections2.push(new PersonSet('id2', 'name3', 'color4'));
    mockPersonSetCollections2.push(new PersonSet('id1', 'name1', 'color1'));
    mockPersonSetCollections2.push({color: '#E0E0E0', id: 'missing-person', name: 'missing-person'});

    expect(mockPersonSetCollections1.getLegend(mockPersonSetCollections1.collections[0]))
      .toStrictEqual(mockPersonSetCollections2);
  });
});

describe('PersonFilter', () => {
  it('should create person filter instance from json', () => {
    const mockPersonFilter1 = PersonFilter.fromJson({
      /* eslint-disable */
      name: {
        name: 'name1',
        from: 'from1',
        source: 'source1',
        source_type: 'sourceType1',
        filter_type: 'filterType1',
        role: 'role1',
      },
      name1: {
        name: 'name2',
        from: 'from2',
        source: 'source2',
        source_type: 'sourceType2',
        filter_type: 'filterType2',
        role: 'role2',
      }
      /* eslint-enable */
    });

    const mockPersonFilter2 = [
      new PersonFilter('name1', 'from1', 'source1', 'sourceType1', 'filterType1', 'role1'),
      new PersonFilter('name2', 'from2', 'source2', 'sourceType2', 'filterType2', 'role2')
    ];

    expect(mockPersonFilter1).toStrictEqual(mockPersonFilter2);
  });
});

describe('Column', () => {
  it('should create column from json', () => {
    expect(new Column('name', 'source', 'format'))
      .toStrictEqual(Column.fromJson({ name: 'name', source: 'source', format: 'format' }));
  });
});

describe('ColumnGroup', () => {
  it('should create column group from json', () => {
    const columnGroupMock1 = new ColumnGroup(
      'name1',
      [
        new Column('name1', 'source1', 'format1'),
        new Column('name2', 'source2', 'format2')
      ]
    );

    const columnGroupMock2 = ColumnGroup.fromJson({
      name: 'name1',
      columns: [
        {
          name: 'name1',
          source: 'source1',
          format: 'format1'
        },
        {
          name: 'name2',
          source: 'source2',
          format: 'format2'
        }
      ]
    });

    expect(columnGroupMock1).toStrictEqual(columnGroupMock2);
  });
});

describe('GenotypeBrowser', () => {
  it('should create genotype browser from json', () => {
    const genotypeMock1 = new GenotypeBrowser(
      false,
      true,
      false,
      false,
      true,
      false,
      true,
      false,
      false,
      [
        new Column('name1', 'source1', 'format1'),
        new Column('name2', 'source2', 'format2')
      ],
      [
        new PersonFilter('personFilter1', 'string1', 'source1', 'sourceType1', 'filterType1', 'role1'),
        new PersonFilter('personFilter2', 'string2', 'source2', 'sourceType2', 'filterType2', 'role2')
      ],
      [
        new PersonFilter('familyFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
        new PersonFilter('familyFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
      ],
      ['inheritance', 'string1'],
      ['selectedInheritance', 'string2'],
      ['variant', 'string3'],
      ['selectedVariant', 'string1'],
      5,
      false,
      false
    );

    /* eslint-disable */
    const genotypeMock2 = GenotypeBrowser.fromJson({
      has_pedigree_selector: false,
      has_present_in_child: true,
      has_present_in_parent: false,
      has_present_in_role: false,
      has_family_filters: true,
      has_family_filters_beta: false,
      has_family_structure_filter: false,
      has_person_filters: true,
      has_person_filters_beta: false,
      has_study_filters: false,
      has_study_types: false,
      table_columns: [
        {
          name: 'name1',
          source: 'source1',
          format: 'format1'
        },
        {
          name: 'name2',
          source: 'source2',
          format: 'format2'
        }
      ],
      person_filters: [
        {
          name: 'personFilter1',
          from: 'string1',
          source: 'source1',
          source_type: 'sourceType1',
          filter_type: 'filterType1',
          role: 'role1',
        },
        {
          name: 'personFilter2',
          from: 'string2',
          source: 'source2',
          source_type: 'sourceType2',
          filter_type: 'filterType2',
          role: 'role2',
        }
      ],
      family_filters: [
        {
          name: 'familyFilter3',
          from: 'string3',
          source: 'source3',
          source_type: 'sourceType3',
          filter_type: 'filterType3',
          role: 'role3',
        },
        {
          name: 'familyFilter4',
          from: 'string4',
          source: 'source4',
          source_type: 'sourceType4',
          filter_type: 'filterType4',
          role: 'role4',
        }
      ],
      inheritance_type_filter: ['inheritance', 'string1'],
      selected_inheritance_type_filter_values: ['selectedInheritance', 'string2'],
      variant_types: ['variant', 'string3'],
      selected_variant_types: ['selectedVariant', 'string1'],
      max_variants_count: 5,
    });
    /* eslint-enable */

    expect(genotypeMock1).toStrictEqual(genotypeMock2);
  });

  it('should create table columns from json', () => {
    const genotypeMock1 = [
      new Column('name1', 'source1', 'format1'),
      new Column('name2', 'source2', 'format2'),
      new ColumnGroup(
        'col2',
        [
          new Column('name3', 'source2', 'format1'),
          new Column('name4', 'source1', 'format2')
        ]
      )
    ];

    const genotypeMock2 = GenotypeBrowser.tableColumnsFromJson([
      {
        name: 'name1',
        source: 'source1',
        format: 'format1'
      },
      {
        name: 'name2',
        source: 'source2',
        format: 'format2'
      },
      {
        name: 'col2',
        columns: [
          {
            name: 'name3',
            source: 'source2',
            format: 'format1'
          },
          {
            name: 'name4',
            source: 'source1',
            format: 'format2'
          }
        ]
      }
    ]);

    expect(genotypeMock1).toStrictEqual(genotypeMock2);
  });

  it('should get the ids', () => {
    const genotypeMock1 = new GenotypeBrowser(
      false,
      true,
      false,
      false,
      true,
      false,
      true,
      false,
      false,
      [
        new Column('name1', 'source1', 'format1'),
        new Column('name2', 'source2', 'format2')
      ],
      [
        new PersonFilter('personFilter1', 'string1', 'source1', 'sourceType1', 'filterType1', 'role1'),
        new PersonFilter('personFilter2', 'string2', 'source2', 'sourceType2', 'filterType2', 'role2')
      ],
      [
        new PersonFilter('familyFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
        new PersonFilter('familyFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
      ],
      ['inheritance', 'string1'],
      ['selectedInheritance', 'string2'],
      ['variant', 'string3'],
      ['selectedVariant', 'string1'],
      5,
      false,
      false
    );

    expect(genotypeMock1.columnIds).toStrictEqual(['source1', 'source2']);
  });
});

describe('GeneBrowser', () => {
  it('should create gene browser from json', () => {
    const mockBrowser1 = new GeneBrowser(
      true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true
    );
    const mockBrowser2 = GeneBrowser.fromJson({
      /* eslint-disable */
      enabled: true,
      frequency_column: 'frequencyCol1',
      frequency_name: 'frequencyName1',
      effect_column: 'effectCol1',
      location_column: 'locationCol1',
      domain_min: 5,
      domain_max: 6,
      has_affected_status: true
      /* eslint-enable */
    });

    expect(mockBrowser1).toStrictEqual(mockBrowser2);
  });
});

describe('Dataset', () => {
  const datasetMock1 = new Dataset(
    'id1',
    'name1',
    ['parent1', 'parent2'],
    false,
    ['study1', 'study2'],
    ['studyName1', 'studyName2'],
    ['studyType1', 'studyType2'],
    'phenotypeData1',
    false,
    true,
    true,
    false,
    {enabled: true},
    new GenotypeBrowser(
      false,
      true,
      false,
      false,
      true,
      false,
      true,
      false,
      false,
      [
        new Column('name1', 'source1', 'format1'),
        new Column('name2', 'source2', 'format2')
      ],
      [
        new PersonFilter('personFilter1', 'string1', 'source1', 'sourceType1', 'filterType1', 'role1'),
        new PersonFilter('personFilter2', 'string2', 'source2', 'sourceType2', 'filterType2', 'role2')
      ],
      [
        new PersonFilter('familyFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
        new PersonFilter('familyFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
      ],
      ['inheritance', 'string1'],
      ['selectedInheritance', 'string2'],
      ['variant', 'string3'],
      ['selectedVariant', 'string1'],
      5,
      false,
      false
    ),
    new PersonSetCollections(
      [
        new PersonSetCollection(
          'id1',
          'name1',
          [
            new PersonSet('id1', 'name1', 'color1'),
            new PersonSet('id1', 'name2', 'color3'),
            new PersonSet('id2', 'name3', 'color4')
          ]
        ),
        new PersonSetCollection(
          'id2',
          'name2',
          [
            new PersonSet('id2', 'name2', 'color2'),
            new PersonSet('id2', 'name3', 'color5'),
            new PersonSet('id3', 'name4', 'color6')
          ]
        )
      ]
    ),
    [
      new UserGroup(3, 'name1', ['user1', 'user2'], [
        {datasetId: 'dataset2', datasetName: 'dataset2'},
        {datasetId: 'dataset3', datasetName: 'dataset3'}
      ]),
      new UserGroup(5, 'name2', ['user12', 'user5'], [
        {datasetId: 'dataset1', datasetName: 'dataset1'},
        {datasetId: 'dataset2', datasetName: 'dataset2'}
      ])
    ],
    new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
    false,
    true,
    true
  );

  const datasetMock2 = new Dataset(
    'id2',
    'name2',
    ['parent2', 'parent2'],
    true,
    ['study2', 'study2'],
    ['studyName2', 'studyName2'],
    ['studyType2', 'studyType2'],
    'phenotypeData2',
    true,
    false,
    true,
    true,
    {enabled: true},
    new GenotypeBrowser(
      true,
      false,
      true,
      false,
      false,
      false,
      true,
      false,
      false,
      [
        new Column('name2', 'source12', 'format2'),
        new Column('name4', 'source2', 'format3')
      ],
      [
        new PersonFilter('personFilter2', 'string3', 'source3', 'sourceType6', 'filterType8', 'role5'),
        new PersonFilter('personFilter2', 'string5', 'source2', 'sourceType2', 'filterType3', 'role6')
      ],
      [
        new PersonFilter('familyFilter6', 'string6', 'source6', 'sourceType6', 'filterType5', 'role3'),
        new PersonFilter('familyFilter5', 'string5', 'source5', 'sourceType2', 'filterType1', 'role0')
      ],
      ['inheritance1', 'string2'],
      ['selectedInheritance3', 'string5'],
      ['variant2', 'string5'],
      ['selectedVariant1', 'string3'],
      6,
      false,
      false
    ),
    new PersonSetCollections([
      new PersonSetCollection(
        'id4',
        'name4',
        [
          new PersonSet('id4', 'name1', 'color1'),
          new PersonSet('id4', 'name2', 'color3'),
          new PersonSet('id2', 'name3', 'color4')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name3',
        [
          new PersonSet('id5', 'name2', 'color2'),
          new PersonSet('id3', 'name7', 'color5'),
          new PersonSet('id5', 'name8', 'color6')
        ]
      )
    ]),
    [
      new UserGroup(9, 'name13', ['user9', 'user6'], [
        {datasetId: 'dataset4', datasetName: 'dataset4'},
        {datasetId: 'dataset3', datasetName: 'dataset3'}
      ]),
      new UserGroup(6, 'name8', ['user10', 'user12'], [
        {datasetId: 'dataset14', datasetName: 'dataset14'},
        {datasetId: 'dataset16', datasetName: 'dataset16'}
      ])
    ],
    new GeneBrowser(false, 'frequencyCol6', 'frequencyName7', 'effectCol4', 'locationCol2', 7, 8, true),
    true,
    true,
    true
  );

  /* eslint-disable */
  const datasetJson1 = {
    id: 'id1',
    description: 'desc1',
    children_description: '',
    name: 'name1',
    parents: ['parent1', 'parent2'],
    access_rights: false,
    studies: ['study1', 'study2'],
    study_names: ['studyName1', 'studyName2'],
    study_types: ['studyType1', 'studyType2'],
    phenotype_data: 'phenotypeData1',
    genotype_browser: false,
    phenotype_tool: true,
    enrichment_tool: true,
    phenotype_browser: false,
    common_report: {enabled: true},
    genotype_browser_config: {
      has_pedigree_selector: false,
      has_present_in_child: true,
      has_present_in_parent: false,
      has_present_in_role: false,
      has_family_filters: true,
      has_family_filters_beta: false,
      has_family_structure_filter: false,
      has_person_filters_beta: false,
      has_person_filters: true,
      has_study_filters: false,
      has_study_types: false,
      table_columns: [
        {
          name: 'name1',
          source: 'source1',
          format: 'format1'
        },
        {
          name: 'name2',
          source: 'source2',
          format: 'format2'
        }
      ],
      person_filters: [
        {
          name: 'personFilter1',
          from: 'string1',
          source: 'source1',
          source_type: 'sourceType1',
          filter_type: 'filterType1',
          role: 'role1',
        },
        {
          name: 'personFilter2',
          from: 'string2',
          source: 'source2',
          source_type: 'sourceType2',
          filter_type: 'filterType2',
          role: 'role2',
        }
      ],
      family_filters: [
        {
          name: 'familyFilter3',
          from: 'string3',
          source: 'source3',
          source_type: 'sourceType3',
          filter_type: 'filterType3',
          role: 'role3',
        },
        {
          name: 'familyFilter4',
          from: 'string4',
          source: 'source4',
          source_type: 'sourceType4',
          filter_type: 'filterType4',
          role: 'role4',
        }
      ],
      inheritance_type_filter: ['inheritance', 'string1'],
      selected_inheritance_type_filter_values: ['selectedInheritance', 'string2'],
      variant_types: ['variant', 'string3'],
      selected_variant_types: ['selectedVariant', 'string1'],
      max_variants_count: 5,
    },
    person_set_collections: {
      id1: {
        name: 'name1',
        domain: [
          {
            id: 'id1',
            name: 'name1',
            color: 'color1'
          },
          {
            id: 'id1',
            name: 'name2',
            color: 'color3'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color4'
          }
        ]
      },
      id2: {
        name: 'name2',
        domain: [
          {
            id: 'id2',
            name: 'name2',
            color: 'color2'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color5'
          },
          {
            id: 'id3',
            name: 'name4',
            color: 'color6'
          }
        ]
      }
    },
    groups: [
      {
        id: 3,
        name: 'name1',
        users: ['user1', 'user2'],
        datasets: [
          {datasetId: 'dataset2', datasetName: 'dataset2'},
          {datasetId: 'dataset3', datasetName: 'dataset3'}
        ]
      },
      {
        id: 5,
        name: 'name2',
        users: ['user12', 'user5'],
        datasets: [
          {datasetId: 'dataset1', datasetName: 'dataset1'},
          {datasetId: 'dataset2', datasetName: 'dataset2'}
        ]
      }
    ],
    gene_browser: {
      enabled: true,
      frequency_column: 'frequencyCol1',
      frequency_name: 'frequencyName1',
      effect_column: 'effectCol1',
      location_column: 'locationCol1',
      domain_min: 5,
      domain_max: 6,
      has_affected_status: true
    },
    has_denovo: false,
    description_editable: true,
    has_transmitted: true,
  };

  const datasetJson2 = {
    id: 'id2',
    description: 'desc2',
    children_description: '',
    name: 'name2',
    parents: ['parent2', 'parent2'],
    access_rights: true,
    studies: ['study2', 'study2'],
    study_names: ['studyName2', 'studyName2'],
    study_types: ['studyType2', 'studyType2'],
    phenotype_data: 'phenotypeData2',
    genotype_browser: true,
    phenotype_tool: false,
    enrichment_tool: true,
    phenotype_browser: true,
    common_report: {enabled: true},
    genotype_browser_config: {
      has_pedigree_selector: true,
      has_present_in_child: false,
      has_present_in_parent: true,
      has_present_in_role: false,
      has_family_filters: false,
      has_family_filters_beta: false,
      has_family_structure_filter: false,
      has_person_filters: true,
      has_person_filters_beta: false,
      has_study_filters: false,
      has_study_types: false,
      table_columns: [
        {
          name: 'name2',
          source: 'source12',
          format: 'format2'
        },
        {
          name: 'name4',
          source: 'source2',
          format: 'format3'
        }
      ],
      person_filters: [
        {
          name: 'personFilter2',
          from: 'string3',
          source: 'source3',
          source_type: 'sourceType6',
          filter_type: 'filterType8',
          role: 'role5',
        },
        {
          name: 'personFilter2',
          from: 'string5',
          source: 'source2',
          source_type: 'sourceType2',
          filter_type: 'filterType3',
          role: 'role6',
        }
      ],
      family_filters: [
        {
          name: 'familyFilter6',
          from: 'string6',
          source: 'source6',
          source_type: 'sourceType6',
          filter_type: 'filterType5',
          role: 'role3',
        },
        {
          name: 'familyFilter5',
          from: 'string5',
          source: 'source5',
          source_type: 'sourceType2',
          filter_type: 'filterType1',
          role: 'role0',
        }
      ],
      inheritance_type_filter: ['inheritance1', 'string2'],
      selected_inheritance_type_filter_values: ['selectedInheritance3', 'string5'],
      variant_types: ['variant2', 'string5'],
      selected_variant_types: ['selectedVariant1', 'string3'],
      max_variants_count: 6,
    },
    person_set_collections: {
      id4: {
        name: 'name4',
        domain: [
          {
            id: 'id4',
            name: 'name1',
            color: 'color1'
          },
          {
            id: 'id4',
            name: 'name2',
            color: 'color3'
          },
          {
            id: 'id2',
            name: 'name3',
            color: 'color4'
          }
        ]
      },
      id2: {
        name: 'name3',
        domain: [
          {
            id: 'id5',
            name: 'name2',
            color: 'color2'
          },
          {
            id: 'id3',
            name: 'name7',
            color: 'color5'
          },
          {
            id: 'id5',
            name: 'name8',
            color: 'color6'
          }
        ]
      }
    },
    groups: [
      {
        id: 9,
        name: 'name13',
        users: ['user9', 'user6'],
        datasets: [
          { datasetId: 'dataset4', datasetName: 'dataset4' },
          { datasetId: 'dataset3', datasetName: 'dataset3' }
        ]
      },
      {
        id: 6,
        name: 'name8',
        users: ['user10', 'user12'],
        datasets: [
          { datasetId: 'dataset14', datasetName: 'dataset14' },
          { datasetId: 'dataset16', datasetName: 'dataset16' }]
      }
    ],
    gene_browser: {
      enabled: false,
      frequency_column: 'frequencyCol6',
      frequency_name: 'frequencyName7',
      effect_column: 'effectCol4',
      location_column: 'locationCol2',
      domain_min: 7,
      domain_max: 8,
      has_affected_status: true
    },
    has_denovo: true,
    description_editable: true,
    has_transmitted: true,
  };
  /* eslint-enable */

  it('should create dataset from json', () => {
    const datasetMockFromJson = Dataset.fromJson(datasetJson1);
    expect(datasetMock1).toStrictEqual(datasetMockFromJson);
  });

  it('should create dataset from json array', () => {
    const datasetMockArray = [datasetMock1, datasetMock2];
    const datasetMockArrayFromJson = Dataset.fromJsonArray([datasetJson1, datasetJson2]);
    expect(datasetMockArray).toStrictEqual(datasetMockArrayFromJson);
  });

  it('should get dataset id', () => {
    expect(datasetMock1.getDefaultGroups()).toStrictEqual(['any_dataset', 'id1']);
  });

  it('should create dataset from dataset and details json\'s', () => {
    /* eslint-disable */
    const datasetMockFromJson = Dataset.fromDataset({
      id: 'id1',
      description: 'desc1',
      children_description: '',
      description_editable: true,
      name: 'name1',
      parents: ['parent1', 'parent2'],
      access_rights: false,
      studies: ['study1', 'study2'],
      study_names: ['studyName1', 'studyName2'],
      study_types: ['studyType1', 'studyType2'],
      phenotype_data: 'phenotypeData1',
      genotype_browser: false,
      phenotype_tool: true,
      enrichment_tool: true,
      phenotype_browser: false,
      common_report: {enabled: true},
      genotype_browser_config: {
        has_pedigree_selector: false,
        has_present_in_child: true,
        has_present_in_parent: false,
        has_present_in_role: false,
        has_family_filters: true,
        has_family_filters_beta: false,
        has_family_structure_filter: false,
        has_person_filters: true,
        has_person_filters_beta: false,
        has_study_filters: false,
        has_study_types: false,
        table_columns: [{
          name: 'name1',
          source: 'source1',
          format: 'format1'
        }, {
          name: 'name2',
          source: 'source2',
          format: 'format2'
        }],
        person_filters: [
          {
            name: 'personFilter1',
            from: 'string1',
            source: 'source1',
            source_type: 'sourceType1',
            filter_type: 'filterType1',
            role: 'role1',
          },
          {
            name: 'personFilter2',
            from: 'string2',
            source: 'source2',
            source_type: 'sourceType2',
            filter_type: 'filterType2',
            role: 'role2',
          }
        ],
        family_filters: [
          {
            name: 'familyFilter3',
            from: 'string3',
            source: 'source3',
            source_type: 'sourceType3',
            filter_type: 'filterType3',
            role: 'role3',
          },
          {
            name: 'familyFilter4',
            from: 'string4',
            source: 'source4',
            source_type: 'sourceType4',
            filter_type: 'filterType4',
            role: 'role4',
          }
        ],
        inheritance_type_filter: ['inheritance', 'string1'],
        selected_inheritance_type_filter_values: ['selectedInheritance', 'string2'],
        variant_types: ['variant', 'string3'],
        selected_variant_types: ['selectedVariant', 'string1'],
        max_variants_count: 5,
      }, person_set_collections: {
        id1: {
          name: 'name1',
          domain: [
            {
              id: 'id1',
              name: 'name1',
              color: 'color1'
            },
            {
              id: 'id1',
              name: 'name2',
              color: 'color3'
            },
            {
              id: 'id2',
              name: 'name3',
              color: 'color4'
            }
          ]
        },
        id2: {
          name: 'name2',
          domain: [
            {
              id: 'id2',
              name: 'name2',
              color: 'color2'
            },
            {
              id: 'id2',
              name: 'name3',
              color: 'color5'
            },
            {
              id: 'id3',
              name: 'name4',
              color: 'color6'
            }
          ]
        }
      }, groups: [
        {
          id: 3,
          name: 'name1',
          users: ['user1', 'user2'],
          datasets: [
            {datasetId: 'dataset2', datasetName: 'dataset2'},
            {datasetId: 'dataset3', datasetName: 'dataset3'}
          ]
        }, {
          id: 5,
          name: 'name2',
          users: ['user12', 'user5'],
          datasets: [
            {datasetId: 'dataset1', datasetName: 'dataset1'},
            {datasetId: 'dataset2', datasetName: 'dataset2'}
          ]
        }
      ], gene_browser: {
        enabled: true,
        frequency_column: 'frequencyCol1',
        frequency_name: 'frequencyName1',
        effect_column: 'effectCol1',
        location_column: 'locationCol1',
        domain_min: 5,
        domain_max: 6,
        has_affected_status: true
      },
      has_denovo: false,
      has_transmitted: true
    });
    /* eslint-enable */
    expect(datasetMock1).toStrictEqual(datasetMockFromJson);
  });
});
