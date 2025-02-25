import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonFiltersBlockComponent } from './person-filters-block.component';
import { StoreModule } from '@ngrx/store';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { Dataset, GenotypeBrowser, Column, PersonFilter,
  PersonSetCollection, PersonSetCollections, PersonSet, GeneBrowser } from 'app/datasets/datasets';
import { UserGroup } from 'app/users-groups/users-groups';
import { PersonAndFamilyFilters, personFiltersReducer } from 'app/person-filters/person-filters.state';
import { personIdsReducer } from 'app/person-ids/person-ids.state';
import { of } from 'rxjs';
import { PersonFilterState } from 'app/person-filters/person-filters';
import { NO_ERRORS_SCHEMA } from '@angular/core';


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
  'genome1',
  true
);

const datasetMock2 = new Dataset(
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
    [],
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
  'genome1',
  true
);

describe('PersonFiltersBlockComponent', () => {
  let component: PersonFiltersBlockComponent;
  let fixture: ComponentFixture<PersonFiltersBlockComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [PersonFiltersBlockComponent],
      imports: [
        StoreModule.forRoot({ personFilters: personFiltersReducer, personIds: personIdsReducer }), NgbNavModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    jest.clearAllMocks();
    jest.clearAllTimers();

    fixture = TestBed.createComponent(PersonFiltersBlockComponent);
    component = fixture.componentInstance;

    component.dataset = datasetMock;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should show advanced button', () => {
    fixture.detectChanges();
    expect(component.showAdvancedButton).toBe(true);
  });

  it('should not show advanced button', () => {
    component.dataset = datasetMock2;
    fixture.detectChanges();
    expect(component.showAdvancedButton).toBe(false);
  });

  it('should select person ids from state', () => {
    fixture.detectChanges();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');

    const personFilters: PersonAndFamilyFilters = {
      familyFilters: null,
      personFilters: null,
    };
    const personIds = ['id1', 'id2'];

    jest.spyOn(rxjs, 'combineLatest').mockReturnValue(of([personFilters, personIds]));
    const ngbSelectSpy = jest.spyOn(component.ngbNav, 'select');

    jest.useFakeTimers();
    const timer: ReturnType<typeof setTimeout> = setTimeout(() => '', 10);
    jest.spyOn(global, 'setTimeout').mockImplementation((fn) => {
      fn();
      return timer;
    });

    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(ngbSelectSpy).toHaveBeenCalledWith('personIds');
    jest.useRealTimers();
  });

  it('should select person filters from state', () => {
    fixture.detectChanges();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');

    const personFilters: PersonAndFamilyFilters = {
      familyFilters: null,
      personFilters: [new PersonFilterState('id1', '', '', '', '', null)],
    };
    const personIds: string[] = [];

    jest.spyOn(rxjs, 'combineLatest').mockReturnValue(of([personFilters, personIds]));
    const ngbSelectSpy = jest.spyOn(component.ngbNav, 'select');

    jest.useFakeTimers();
    const timer: ReturnType<typeof setTimeout> = setTimeout(() => '', 10);
    jest.spyOn(global, 'setTimeout').mockImplementation((fn) => {
      fn();
      return timer;
    });

    component.ngAfterViewInit();
    jest.runAllTimers();

    expect(ngbSelectSpy).toHaveBeenCalledWith('advanced');
  });

  it('should dispatch reset methods when changing tabs', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.onNavChange();
    expect(dispatchSpy).toHaveBeenCalledWith({
      type: '[Genotype] Reset personFilters states'
    });
    expect(dispatchSpy).toHaveBeenCalledWith({
      type: '[Genotype] Reset person ids',
    });
  });
});
