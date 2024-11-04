import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import { UsersService } from 'app/users/users.service';
import { MultiContinuousFilterComponent } from './multi-continuous-filter.component';
import { Observable, of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { PhenoMeasure } from 'app/pheno-browser/pheno-browser';
import {
  MatAutocompleteOrigin,
  MatAutocomplete,
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { Store, StoreModule } from '@ngrx/store';
import {
  personFiltersReducer,
  removeFamilyFilter,
  removePersonFilter,
  updateFamilyFilter,
  updatePersonFilter } from 'app/person-filters/person-filters.state';
import { ContinuousFilterState, ContinuousSelection, PersonFilterState } from 'app/person-filters/person-filters';
import { ContinuousMeasure } from 'app/measures/measures';

const selectionMock = {
  isEmpty: (): boolean => true,
};

const personFilterMock = {
  id: '',
  name: '',
  from: '',
  source: '',
  sourceType: '',
  role: '',
  filterType: '',
  domain: [''],
  // eslint-disable-next-line @typescript-eslint/no-empty-function, @typescript-eslint/explicit-function-return-type
  isEmpty: (): boolean => true,
  selection: selectionMock
};

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

describe('MultiContinuousFilterComponent', () => {
  let component: MultiContinuousFilterComponent;
  let fixture: ComponentFixture<MultiContinuousFilterComponent>;
  const mockDatasetsService = new MockDatasetsService();
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        MultiContinuousFilterComponent,
        PhenoMeasureSelectorComponent
      ],
      providers: [
        MultiContinuousFilterComponent,
        {provide: MeasuresService, useValue: {getContinuousMeasures: (): Observable<PhenoMeasure[]> => of()}},
        HttpClientTestingModule,
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''}
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({personFilters: personFiltersReducer}),
        FormsModule,
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(MultiContinuousFilterComponent);
    component = fixture.componentInstance;
    component.continuousFilter = personFilterMock;
    component.datasetId = '';

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    jest.spyOn(store, 'select').mockReturnValue(of({
      familyFilters: [
        new PersonFilterState(
          'familyName1',
          'continuous',
          'familyRole',
          'familySource',
          'familyFrom',
          new ContinuousSelection(1, 2, 3, 4),
        ),
        new PersonFilterState(
          'familyName2',
          'continuous',
          'familyRole',
          'familySource',
          'familyFrom',
          new ContinuousSelection(1, 2, 3, 4),
        )
      ],
      personFilters: [
        new PersonFilterState(
          'personName1',
          'continuous',
          'personRole',
          'personSource',
          'personFrom',
          new ContinuousSelection(1, 2, 3, 4),
        ),
        new PersonFilterState(
          'personName2',
          'continuous',
          'personRole',
          'personSource',
          'personFrom',
          new ContinuousSelection(1, 2, 3, 4),
        )]
    }));
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set the current continuous filter when the family filters '
    + 'from state do not contain the id of the given filter', () => {
    component.isFamilyFilters = true;
    const filter = {
      id: 'filterId',
      type: '',
      role: '',
      from: '',
      source: '',
      sourceType: '',
      selection: selectionMock,
      isEmpty: (): boolean => true,
      min: 0,
      max: 0,
      domainMin: 0,
      domainMax: 0
    } as ContinuousFilterState;
    component.continuousFilter = filter;

    component.ngOnInit();
    expect(component.continuousFilterState).toStrictEqual(filter);
  });

  it('should set the current continuous filter state to be a filter from family filters', () => {
    component.isFamilyFilters = true;
    component.continuousFilter = {
      id: 'familyName2',
      type: '',
      role: '',
      from: '',
      source: '',
      sourceType: '',
      selection: selectionMock,
      isEmpty: (): boolean => true,
      min: 0,
      max: 0,
      domainMin: 0,
      domainMax: 0
    } as ContinuousFilterState;

    component.ngOnInit();
    expect(component.continuousFilterState).toStrictEqual(
      new PersonFilterState(
        'familyName2',
        'continuous',
        'familyRole',
        'familySource',
        'familyFrom',
        new ContinuousSelection(1, 2, 3, 4),
      ),
    );
  });

  it('should set the current continuous filter state to be a filter from person filters', () => {
    component.isFamilyFilters = false;
    component.continuousFilter = {
      id: 'personName2',
      type: '',
      role: '',
      from: '',
      source: '',
      sourceType: '',
      selection: selectionMock,
      isEmpty: (): boolean => true,
      min: 0,
      max: 0,
      domainMin: 0,
      domainMax: 0
    } as ContinuousFilterState;

    component.ngOnInit();
    expect(component.continuousFilterState).toStrictEqual(
      new PersonFilterState(
        'personName2',
        'continuous',
        'personRole',
        'personSource',
        'personFrom',
        new ContinuousSelection(1, 2, 3, 4),
      ),
    );
  });


  it('should set the current continuous filter when the family filters or person filters from state are empty', () => {
    jest.clearAllMocks();
    jest.spyOn(store, 'select').mockReturnValue(of({
      familyFilters: null,
      personFilters: null
    }));
    const filter = {
      id: 'filterId',
      type: '',
      role: '',
      from: '',
      source: '',
      sourceType: '',
      selection: selectionMock,
      isEmpty: (): boolean => true,
      min: 0,
      max: 0,
      domainMin: 0,
      domainMax: 0
    } as ContinuousFilterState;
    component.continuousFilter = filter;
    component.isFamilyFilters = true;

    component.ngOnInit();
    expect(component.continuousFilterState).toStrictEqual(filter);

    component.isFamilyFilters = false;

    component.ngOnInit();
    expect(component.continuousFilterState).toStrictEqual(filter);
  });

  it('should set selected measure when in family filters tab', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');

    component.isFamilyFilters = true;

    component.ngOnInit();

    const measure = new ContinuousMeasure('m1', 5, 10);
    component.selectedMeasure = measure;
    expect(component.internalSelectedMeasure).toStrictEqual(measure);
    expect(component.continuousFilterState.source).toBe('m1');
    expect(component.continuousFilterState.selection['min']).toBe(5);
    expect(component.continuousFilterState.selection['max']).toBe(10);
    expect(dispatchSpy).toHaveBeenCalledWith(updateFamilyFilter({familyFilter: component.continuousFilterState}));
  });

  it('should set selected measure when in person filters tab', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.isFamilyFilters = false;

    component.ngOnInit();

    const measure = new ContinuousMeasure('m2', 3, 11);
    component.selectedMeasure = measure;
    expect(component.internalSelectedMeasure).toStrictEqual(measure);
    expect(component.continuousFilterState.source).toBe('m2');
    expect(component.continuousFilterState.selection['min']).toBe(3);
    expect(component.continuousFilterState.selection['max']).toBe(11);
    expect(dispatchSpy).toHaveBeenCalledWith(updatePersonFilter({personFilter: component.continuousFilterState}));
  });

  it('should set selected measure when measure is null and when in family filters', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.isFamilyFilters = true;

    component.ngOnInit();

    component.selectedMeasure = null;
    expect(component.internalSelectedMeasure).toBeNull();
    expect(dispatchSpy).toHaveBeenCalledWith(removeFamilyFilter({familyFilter: component.continuousFilterState}));
  });

  it('should set selected measure when measure is null and when in person filters', () => {
    const dispatchSpy = jest.spyOn(component['store'], 'dispatch');
    component.isFamilyFilters = false;

    component.ngOnInit();

    component.selectedMeasure = null;
    expect(component.internalSelectedMeasure).toBeNull();
    expect(dispatchSpy).toHaveBeenCalledWith(removePersonFilter({personFilter: component.continuousFilterState}));
  });

  it('should get selected measure', () => {
    const measure = new ContinuousMeasure('m2', 3, 11);
    component.internalSelectedMeasure = measure;
    expect(component.selectedMeasure).toStrictEqual(measure);
  });
});
