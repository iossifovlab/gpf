import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { PhenoBrowserService } from 'app/pheno-browser/pheno-browser.service';
import { UsersService } from 'app/users/users.service';
import { CategoricalFilterComponent } from './categorical-filter.component';
import { APP_BASE_HREF } from '@angular/common';
import { Store, StoreModule } from '@ngrx/store';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { CategoricalFilterState, CategoricalSelection, PersonFilterState } from 'app/person-filters/person-filters';
import { cloneDeep } from 'lodash';
import { Observable, of } from 'rxjs';
import {
  removeFamilyFilter,
  removePersonFilter,
  updateFamilyFilter,
  updatePersonFilter } from 'app/person-filters/person-filters.state';

const mockPersonAndFamilyFiltersState = {
  familyFilters: [
    new PersonFilterState(
      'familyName1',
      'categorical',
      'familyRole1',
      'familySource1',
      'familyFrom1',
      new CategoricalSelection(['selection1'])
    ),
    new PersonFilterState(
      'familyName2',
      'categorical',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new CategoricalSelection(['selection2'])
    )
  ],
  personFilters: [
    new PersonFilterState(
      'personName1',
      'categorical',
      'personRole1',
      'personSource1',
      'personFrom1',
      new CategoricalSelection(['selection1'])
    ),
    new PersonFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'personFrom2',
      new CategoricalSelection(['selection2'])
    )
  ],
};

const measureDescMock = {
  instrument_name: 'ssc_commonly_used',
  measure_name: 'race_parents',
  measure_type: 'categorical',
  values_domain: [
    'african-amer',
    'asian',
    'more-than-one-race',
    'native-american',
    'native-hawaiian',
    'not-specified',
    'other',
    'white'
  ]
};

class MockPhenoBrowserService {
  public getMeasureDescription(datasetId: string, source: string): Observable<object> {
    return of(measureDescMock);
  }
}

describe('CategoricalFilterComponent', () => {
  let component: CategoricalFilterComponent;
  let fixture: ComponentFixture<CategoricalFilterComponent>;
  let store: Store;
  const mockPhenoBrowserService = new MockPhenoBrowserService();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [CategoricalFilterComponent],
      providers: [
        DatasetsService,
        { provide: PhenoBrowserService, useValue: mockPhenoBrowserService },
        ConfigService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule, FormsModule,
        StoreModule.forRoot({datasetId: datasetIdReducer})
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CategoricalFilterComponent);
    component = fixture.componentInstance;
    store = TestBed.inject(Store);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get family filters from state', () => {
    component.isFamilyFilters = true;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep(mockPersonAndFamilyFiltersState)));
    const filter = new CategoricalFilterState(
      'familyName2',
      'categorical',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new CategoricalSelection(['selection1'])
    );
    component.categoricalFilter = filter;
    component.ngOnInit();
    expect(component.categoricalFilterState).toStrictEqual(
      new PersonFilterState(
        'familyName2',
        'categorical',
        'familyRole2',
        'familySource2',
        'familyFrom2',
        new CategoricalSelection(['selection2'])
      )
    );
  });

  it('should get person filters from state', () => {
    component.isFamilyFilters = false;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep(mockPersonAndFamilyFiltersState)));
    const filter = new CategoricalFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'personFrom2',
      new CategoricalSelection(['selection1'])
    );
    component.categoricalFilter = filter;
    component.ngOnInit();
    expect(component.categoricalFilterState).toStrictEqual(
      new PersonFilterState(
        'personName2',
        'categorical',
        'personRole2',
        'personSource2',
        'personFrom2',
        new CategoricalSelection(['selection2'])
      ));
  });

  it('should use the filter passed by parent when family or person filters in state are null', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.isFamilyFilters = true;
    component.ngOnInit();
    expect(component.categoricalFilterState).toBeUndefined();

    component.isFamilyFilters = false;
    component.ngOnInit();
    expect(component.categoricalFilterState).toBeUndefined();
  });

  it('should get measure description when the filter is from phenodb', () => {
    component.isFamilyFilters = false;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    const filter = new CategoricalFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'phenodb',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilter = filter;
    component.ngOnInit();
    expect(component.categoricalFilterState).toStrictEqual(
      new CategoricalFilterState(
        'personName2',
        'categorical',
        'personRole2',
        'personSource2',
        'phenodb',
        new CategoricalSelection(['selection2'])
      ));
    expect(component.valuesDomain).toStrictEqual([
      'african-amer',
      'asian',
      'more-than-one-race',
      'native-american',
      'native-hawaiian',
      'not-specified',
      'other',
      'white'
    ]);
  });

  it('should get pedigree column details when the filter is from pedigree', () => {
    component.isFamilyFilters = false;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    const filter = new CategoricalFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'pedigree',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilter = filter;
    component.ngOnInit();
    expect(component.categoricalFilterState).toStrictEqual(
      new CategoricalFilterState(
        'personName2',
        'categorical',
        'personRole2',
        'personSource2',
        'pedigree',
        new CategoricalSelection(['selection2'])
      ));
  });

  it('should set selected value when working with family filters', () => {
    component.isFamilyFilters = true;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    const dispatchSpy = jest.spyOn(store, 'dispatch');

    const filter = new CategoricalFilterState(
      'familyName2',
      'categorical',
      'familyRole2',
      'familySource2',
      'pedigree',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilterState = filter;
    component.selectedValue = 'newFamilySelection';
    expect(component.categoricalFilterState.selection['selection']).toStrictEqual(['newFamilySelection']);
    expect(dispatchSpy).toHaveBeenCalledWith(updateFamilyFilter({familyFilter: cloneDeep(filter)}));
  });

  it('should set selected value when working with person filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    const filter = new CategoricalFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'pedigree',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilterState = filter;
    component.selectedValue = 'newPersonSelection';
    expect(component.categoricalFilterState.selection['selection']).toStrictEqual(['newPersonSelection']);
    expect(dispatchSpy).toHaveBeenCalledWith(updatePersonFilter({personFilter: cloneDeep(filter)}));
  });

  it('should get selected value', () => {
    const filter = new CategoricalFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'pedigree',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilterState = filter;
    expect(component.selectedValue).toBe('selection2');
  });

  it('should clear selected value from family filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    const filter = new CategoricalFilterState(
      'familyName2',
      'categorical',
      'familyRole2',
      'familySource2',
      'pedigree',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilterState = filter;

    component.isFamilyFilters = true;
    component.clear();
    expect(dispatchSpy).toHaveBeenCalledWith(removeFamilyFilter({familyFilter: cloneDeep(filter)}));
  });

  it('should clear selected value from person filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');

    const filter = new CategoricalFilterState(
      'personName2',
      'categorical',
      'personRole2',
      'personSource2',
      'pedigree',
      new CategoricalSelection(['selection2'])
    );
    component.categoricalFilterState = filter;

    component.isFamilyFilters = false;
    component.clear();
    expect(dispatchSpy).toHaveBeenCalledWith(removePersonFilter({personFilter: cloneDeep(filter)}));
  });
});
