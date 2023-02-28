import { ComponentFixture, TestBed } from '@angular/core/testing';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import {
  Column, Dataset, GeneBrowser, GenotypeBrowser, PersonFilter,
  PersonSet, PersonSetCollection, PersonSetCollections
} from 'app/datasets/datasets';
import { UserGroup } from 'app/users-groups/users-groups';

import { StudyFiltersTreeComponent } from './treelist-checkbox.component';

const datasetMock = new Dataset(
  'id1',
  'desc1',
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
    new Set(['inheritance', 'string1']),
    new Set(['selectedInheritance', 'string2']),
    new Set(['variant', 'string3']),
    new Set(['selectedVariant', 'string1']),
    5
  ),
  new PersonSetCollections(
    [
      new PersonSetCollection(
        'id1',
        'name1',
        'id1',
        new PersonSet('id1', 'name1', ['value1', 'value2'], 'color1'),
        [
          new PersonSet('id1', 'name2', ['value2', 'value2'], 'color3'),
          new PersonSet('id2', 'name3', ['value2', 'value3'], 'color4')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name2',
        'id2',
        new PersonSet('id2', 'name2', ['value3', 'value4'], 'color2'),
        [
          new PersonSet('id2', 'name3', ['value3', 'value3'], 'color5'),
          new PersonSet('id3', 'name4', ['value3', 'value4'], 'color6')
        ]
      )
    ]
  ),
  [
    new UserGroup(3, 'name1', ['user1', 'user2'], [{datasetName: 'dataset1', datasetId: 'dataset2'}]),
    new UserGroup(5, 'name2', ['user12', 'user5'], [{datasetName: 'dataset1', datasetId: 'dataset2'}])
  ],
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  'genome1'
);

describe('StudyFiltersTreeComponent', () => {
  let component: StudyFiltersTreeComponent;
  let fixture: ComponentFixture<StudyFiltersTreeComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [StudyFiltersTreeComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(StudyFiltersTreeComponent);
    component = fixture.componentInstance;
    component.data = new DatasetNode(datasetMock, []);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get all childrens of dataset', () => {
    const node1 = new DatasetNode(datasetMock, [new Dataset(
      'id2',
      'desc2',
      'name2',
      ['parent3', 'parent4'],
      true,
      ['study3', 'study4'],
      ['studyName3', 'studyName4'],
      ['studyType3', 'studyType4'],
      'phenotypeData2',
      true,
      false,
      false,
      true,
      {enabled: false},
      new GenotypeBrowser(
        true,
        false,
        true,
        true,
        false,
        true,
        false,
        true,
        true,
        [
          new Column('name3', 'source3', 'format3'),
          new Column('name4', 'source4', 'format4')
        ],
        [
          new PersonFilter('personFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
          new PersonFilter('personFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
        ],
        [
          new PersonFilter('familyFilter5', 'string5', 'source5', 'sourceType5', 'filterType5', 'role5'),
          new PersonFilter('familyFilter6', 'string6', 'source6', 'sourceType6', 'filterType6', 'role6')
        ],
        new Set(['inheritance2', 'string2']),
        new Set(['selectedInheritance2', 'string3']),
        new Set(['variant2', 'string4']),
        new Set(['selectedVariant2', 'string2']),
        6
      ),
      new PersonSetCollections(
        [
          new PersonSetCollection(
            'id3',
            'name3',
            'id3',
            new PersonSet('id3', 'name3', ['value5', 'value6'], 'color7'),
            [
              new PersonSet('id3', 'name4', ['value6, value7'], 'color9'),
              new PersonSet('id4', 'name5', ['value7, value8'], 'color10')
            ]
          ),
          new PersonSetCollection(
            'id4',
            'name4',
            'id4',
            new PersonSet('id4', 'name4', ['value9, value10'], 'color8'),
            [
              new PersonSet('id4', 'name5', ['value9, value9'], 'color11'),
              new PersonSet('id5', 'name6', ['value9, value10'], 'color12')
            ]
          )
        ]
      ),
      [
        new UserGroup(7, 'name3', ['user7, user8'], [{datasetName: 'dataset3', datasetId: 'dataset4'}]),
        new UserGroup(9, 'name4', ['user14, user10'], [{datasetName: 'dataset3', datasetId: 'dataset4'}])
      ],
      new GeneBrowser(false, 'frequencyCol2', 'frequencyName2', 'effectCol2', 'locationCol2', 7, 8, false),
      true,
      'genome2'
    )]);

    const node2 = new DatasetNode(new Dataset(
      'id2',
      'desc3',
      'name3',
      ['parent5', 'parent6'],
      false,
      ['study5', 'study6'],
      ['studyName5', 'studyName6'],
      ['studyType5', 'studyType6'],
      'phenotypeData3',
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
          new Column('name5', 'source5', 'format5'),
          new Column('name6', 'source6', 'format6')
        ],
        [
          new PersonFilter('personFilter5', 'string5', 'source5', 'sourceType5', 'filterType5', 'role5'),
          new PersonFilter('personFilter6', 'string6', 'source6', 'sourceType6', 'filterType6', 'role6')
        ],
        [
          new PersonFilter('familyFilter7', 'string7', 'source7', 'sourceType7', 'filterType7', 'role7'),
          new PersonFilter('familyFilter8', 'string8', 'source8', 'sourceType8', 'filterType8', 'role8')
        ],
        new Set(['inheritance3', 'string3']),
        new Set(['selectedInheritance3', 'string4']),
        new Set(['variant3', 'string5']),
        new Set(['selectedVariant3', 'string3']),
        7
      ),
      new PersonSetCollections(
        [
          new PersonSetCollection(
            'id5',
            'name5',
            'id5',
            new PersonSet('id5', 'name5', ['value11, value12'], 'color13'),
            [
              new PersonSet('id5', 'name6', ['value12, value13'], 'color15'),
              new PersonSet('id6', 'name7', ['value13, value14'], 'color16')
            ]
          ),
          new PersonSetCollection(
            'id6',
            'name6',
            'id6',
            new PersonSet('id6', 'name6', ['value15, value16'], 'color14'),
            [
              new PersonSet('id6', 'name7', ['value15', 'value15'], 'color17'),
              new PersonSet('id7', 'name8', ['value15', 'value16'], 'color18')
            ]
          )
        ]
      ),
      [
        new UserGroup(11, 'name5', ['user11, user12'], [{datasetName: 'dataset5', datasetId: 'dataset6'}]),
        new UserGroup(13, 'name6', ['user16, user12'], [{datasetName: 'dataset5', datasetId: 'dataset6'}])
      ],
      new GeneBrowser(true, 'frequencyCol3', 'frequencyName3', 'effectCol3', 'locationCol3', 9, 10, true),
      false,
      'genome3'
    ), [new Dataset(
      'id4',
      'desc4',
      'name4',
      ['parent7', 'parent8'],
      true,
      ['study7', 'study8'],
      ['studyName7', 'studyName8'],
      ['studyType7', 'studyType8'],
      'phenotypeData4',
      true,
      false,
      false,
      true,
      {enabled: false},
      new GenotypeBrowser(
        true,
        false,
        true,
        true,
        false,
        true,
        false,
        true,
        true,
        [
          new Column('name7', 'source7', 'format7'),
          new Column('name8', 'source8', 'format8')
        ],
        [
          new PersonFilter('personFilter7', 'string7', 'source7', 'sourceType7', 'filterType7', 'role7'),
          new PersonFilter('personFilter8', 'string8', 'source8', 'sourceType8', 'filterType8', 'role8')
        ],
        [
          new PersonFilter('familyFilter9', 'string9', 'source9', 'sourceType9', 'filterType9', 'role9'),
          new PersonFilter('familyFilter10', 'string10', 'source10', 'sourceType10', 'filterType10', 'role10')
        ],
        new Set(['inheritance4', 'string4']),
        new Set(['selectedInheritance4', 'string5']),
        new Set(['variant4', 'string6']),
        new Set(['selectedVariant4', 'string4']),
        8
      ),
      new PersonSetCollections(
        [
          new PersonSetCollection(
            'id7',
            'name7',
            'id7',
            new PersonSet('id7', 'name7', ['value17', 'value18'], 'color19'),
            [
              new PersonSet('id7', 'name8', ['value18', 'value19'], 'color21'),
              new PersonSet('id8', 'name9', ['value19', 'value20'], 'color22')
            ]
          ),
          new PersonSetCollection(
            'id8',
            'name8',
            'id8',
            new PersonSet('id8', 'name8', ['value21', 'value22'], 'color20'),
            [
              new PersonSet('id8', 'name9', ['value21', 'value21'], 'color23'),
              new PersonSet('id9', 'name10', ['value21', 'value22'], 'color24')
            ]
          )
        ]
      ),
      [
        new UserGroup(15, 'name7', ['user15, user16'], [{datasetName: 'dataset7', datasetId: 'dataset8'}]),
        new UserGroup(17, 'name8', ['user18, user16'], [{datasetName: 'dataset7', datasetId: 'dataset8'}])
      ],
      new GeneBrowser(false, 'frequencyCol4', 'frequencyName4', 'effectCol4', 'locationCol4', 11, 12, false),
      true,
      'genome4'
    )]);

    expect(component.getAllChildren([node1, node2])).toStrictEqual(new Set<string>(['id1', 'id2']));
  });
});
