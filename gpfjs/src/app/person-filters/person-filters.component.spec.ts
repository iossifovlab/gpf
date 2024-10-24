import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { PersonFiltersComponent } from './person-filters.component';
import { personFiltersReducer } from './person-filters.state';
import { Store, StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { Dataset, PersonFilter } from 'app/datasets/datasets';
import { of } from 'rxjs';
import { cloneDeep } from 'lodash';
import {
  CategoricalFilterState,
  CategoricalSelection,
  ContinuousFilterState,
  ContinuousSelection,
  PersonFilterState
} from './person-filters';
import { NO_ERRORS_SCHEMA } from '@angular/core';

const mockDataset = {
  id: 'mockDatasetId',
  genotypeBrowserConfig: {
    familyFilters: [
      new PersonFilter(
        'familyName1',
        'familyFrom1',
        'familySource1',
        'categorical',
        'familyFilterType1',
        'familyRole1',
      ),
      new PersonFilter(
        'familyName2',
        'familyFrom2',
        'familySource2',
        'continuous',
        'familyFilterType2',
        'familyRole2',
      ),
      new PersonFilter(
        'familyName3',
        'familyFrom3',
        'familySource3',
        null,
        'familyFilterType3',
        'familyRole3',
      ),
      new PersonFilter(
        'familyName5',
        'familyFrom5',
        'familySource5',
        'continuous',
        'familyFilterType5',
        'familyRole5',
      ),
    ],
    personFilters: [
      new PersonFilter(
        'personName1',
        'personFrom1',
        'personSource1',
        'categorical',
        'personFilterType1',
        'personRole1',
      ),
      new PersonFilter(
        'personName2',
        'personFrom2',
        'personSource2',
        'continuous',
        'personFilterType2',
        'personRole2',
      ),
      new PersonFilter(
        'personName3',
        'personFrom3',
        'personSource3',
        'non-exisitng type',
        'personFilterType3',
        'personRole3',
      ),
    ]
  }
};

const mockPersonAndFamilyFiltersState = {
  familyFilters: [
    new PersonFilterState(
      'familyName1',
      'categorical',
      'familyRole1',
      'familySource1',
      'familyFrom1',
      new CategoricalSelection(['familySelection1']),
    ),
    new PersonFilterState(
      'familyName3',
      'categorical',
      'familyRole3',
      'familySource3',
      'familyFrom3',
      new CategoricalSelection(['familySelection3']),
    ),
    new PersonFilterState(
      'familyName4',
      'continuous',
      'familyRole4',
      'familySource4',
      'familyFrom4',
      new ContinuousSelection(1, 2, 3, 4),
    ),
    new PersonFilterState(
      'familyName5',
      'continuous',
      'familyRole5',
      'familySource5',
      'familyFrom5',
      new ContinuousSelection(1, 2, 3, 4),
    ),
  ],
  personFilters: [
    new PersonFilterState(
      'personName1',
      'continuous',
      'personRole1',
      'personSource1',
      'personFrom1',
      new ContinuousSelection(5, 6, 7, 8),
    ),
    new PersonFilterState(
      'personName3',
      'categorical',
      'personRole3',
      'personSource3',
      'personFrom3',
      new CategoricalSelection(['personSelection3']),
    ),
    new PersonFilterState(
      'personName4',
      'continuous',
      'personRole4',
      'personSource4',
      'personFrom4',
      new ContinuousSelection(5, 6, 7, 8),
    ),
  ],
};

describe('PersonFiltersComponent', () => {
  let component: PersonFiltersComponent;
  let fixture: ComponentFixture<PersonFiltersComponent>;
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PersonFiltersComponent, ErrorsAlertComponent],
      imports: [
        StoreModule.forRoot({personFilters: personFiltersReducer, datasetId: datasetIdReducer})
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(PersonFiltersComponent);
    component = fixture.componentInstance;

    component.dataset = cloneDeep(mockDataset) as Dataset;
    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of({
      familyFilters: null,
      personFilters: null,
    }));
  }));

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should initialize with default family filters', () => {
    component.isFamilyFilters = true;
    fixture.detectChanges();

    expect(component.areFiltersSelected).toBeFalsy();
    expect(component.categoricalFilters).toStrictEqual([
      new CategoricalFilterState(
        'familyName1',
        'categorical',
        'familyRole1',
        'familySource1',
        'familyFrom1',
        new CategoricalSelection([]),
      )
    ]);
    expect(component.continuousFilters).toStrictEqual([
      new ContinuousFilterState(
        'familyName2',
        'continuous',
        'familyRole2',
        'familySource2',
        'familyFrom2',
        new ContinuousSelection(null, null, null, null),
      ),
      new ContinuousFilterState(
        'familyName5',
        'continuous',
        'familyRole5',
        'familySource5',
        'familyFrom5',
        new ContinuousSelection(null, null, null, null),
      ),
    ]);
  });

  it('should initialize with default person filters', () => {
    component.isFamilyFilters = false;
    fixture.detectChanges();

    expect(component.areFiltersSelected).toBeFalsy();
    expect(component.categoricalFilters).toStrictEqual([
      new CategoricalFilterState(
        'personName1',
        'categorical',
        'personRole1',
        'personSource1',
        'personFrom1',
        new CategoricalSelection([]),
      )
    ]);
    expect(component.continuousFilters).toStrictEqual([
      new ContinuousFilterState(
        'personName2',
        'continuous',
        'personRole2',
        'personSource2',
        'personFrom2',
        new ContinuousSelection(null, null, null, null),
      )
    ]);
  });

  it('should initialize with state person filters', () => {
    component.isFamilyFilters = false;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep(mockPersonAndFamilyFiltersState)));
    fixture.detectChanges();

    expect(component.areFiltersSelected).toBeTruthy();
    expect(component.categoricalFilters).toStrictEqual([
      new CategoricalFilterState(
        'personName1',
        'categorical',
        'personRole1',
        'personSource1',
        'personFrom1',
        new CategoricalSelection([]),
      ),
      new PersonFilterState(
        'personName3',
        'categorical',
        'personRole3',
        'personSource3',
        'personFrom3',
        new CategoricalSelection(['personSelection3']),
      )
    ]);
    expect(component.continuousFilters).toStrictEqual([
      new ContinuousFilterState(
        'personName2',
        'continuous',
        'personRole2',
        'personSource2',
        'personFrom2',
        new ContinuousSelection(null, null, null, null),
      ),
      new PersonFilterState(
        'personName1',
        'continuous',
        'personRole1',
        'personSource1',
        'personFrom1',
        new ContinuousSelection(5, 6, 7, 8),
      ),
      new PersonFilterState(
        'personName4',
        'continuous',
        'personRole4',
        'personSource4',
        'personFrom4',
        new ContinuousSelection(5, 6, 7, 8),
      )
    ]);
  });

  it('should initialize with state family filters', () => {
    component.isFamilyFilters = true;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep(mockPersonAndFamilyFiltersState)));
    fixture.detectChanges();

    expect(component.areFiltersSelected).toBeTruthy();
    expect(component.categoricalFilters).toStrictEqual([
      new PersonFilterState(
        'familyName1',
        'categorical',
        'familyRole1',
        'familySource1',
        'familyFrom1',
        new CategoricalSelection(['familySelection1']),
      ),
      new PersonFilterState(
        'familyName3',
        'categorical',
        'familyRole3',
        'familySource3',
        'familyFrom3',
        new CategoricalSelection(['familySelection3']),
      ),
    ]);
    expect(component.continuousFilters).toStrictEqual([
      new ContinuousFilterState(
        'familyName2',
        'continuous',
        'familyRole2',
        'familySource2',
        'familyFrom2',
        new ContinuousSelection(null, null, null, null),
      ),
      new PersonFilterState(
        'familyName5',
        'continuous',
        'familyRole5',
        'familySource5',
        'familyFrom5',
        new ContinuousSelection(1, 2, 3, 4),
      ),
      new PersonFilterState(
        'familyName4',
        'continuous',
        'familyRole4',
        'familySource4',
        'familyFrom4',
        new ContinuousSelection(1, 2, 3, 4),
      ),
    ]);
  });

  it('should console error when trying to add filter from state with unknown type', () => {
    component.isFamilyFilters = true;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: [
        new PersonFilterState(
          'familyName12',
          'unknown',
          'familyRole12',
          'familySource12',
          'familyFrom12',
          new CategoricalSelection(['familySelection12']),
        )
      ],
      personFilters: [
        new PersonFilterState(
          'personName12',
          'non-existing type',
          'personRole12',
          'personSource12',
          'personFrom12',
          new ContinuousSelection(5, 6, 7, 8),
        )
      ]
    })));
    fixture.detectChanges();

    expect(component.categoricalFilters).toStrictEqual([
      new CategoricalFilterState(
        'familyName1',
        'categorical',
        'familyRole1',
        'familySource1',
        'familyFrom1',
        new CategoricalSelection([]),
      ),
    ]);
    expect(component.continuousFilters).toStrictEqual([
      new ContinuousFilterState(
        'familyName2',
        'continuous',
        'familyRole2',
        'familySource2',
        'familyFrom2',
        new ContinuousSelection(null, null, null, null),
      ),
      new ContinuousFilterState(
        'familyName5',
        'continuous',
        'familyRole5',
        'familySource5',
        'familyFrom5',
        new ContinuousSelection(null, null, null, null),
      ),
    ]);
  });
});
