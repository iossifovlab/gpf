import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonFiltersSelectorComponent } from './person-filters-selector.component';
import { StoreModule } from '@ngrx/store';
import { MeasuresService } from 'app/measures/measures.service';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { Column, Dataset, GeneBrowser, GenotypeBrowser, PersonFilter, PersonSet, PersonSetCollection, PersonSetCollections } from 'app/datasets/datasets';
import { UserGroup } from 'app/users-groups/users-groups';

const datasetMock = new Dataset(
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
    new UserGroup(3, 'name1', ['user1', 'user2'], [{datasetName: 'dataset2', datasetId: 'dataset3'}]),
    new UserGroup(5, 'name2', ['user12', 'user5'], [{datasetName: 'dataset1', datasetId: 'dataset2'}])
  ],
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  'genome1',
  true,
);

describe('PersonFiltersSelectorComponent', () => {
  let component: PersonFiltersSelectorComponent;
  let fixture: ComponentFixture<PersonFiltersSelectorComponent>;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PersonFiltersSelectorComponent],
      imports: [StoreModule.forRoot()],
      providers: [ConfigService, MeasuresService, provideHttpClient()]
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFiltersSelectorComponent);
    component = fixture.componentInstance;

    component.dataset = datasetMock;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
