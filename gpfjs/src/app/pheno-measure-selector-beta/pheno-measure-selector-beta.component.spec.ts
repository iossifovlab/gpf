import { provideHttpClientTesting } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, fakeAsync, TestBed, tick, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';

import {
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocomplete,
  MatAutocompleteOrigin,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { Store, StoreModule } from '@ngrx/store';
import { Measure } from 'app/measures/measures';
import { of, Subscription } from 'rxjs';
import { PhenoMeasureSelectorBetaComponent } from './pheno-measure-selector-beta.component';
import { MeasureHistogramState } from 'app/person-filters-selector/measure-histogram.state';
import { CdkVirtualScrollViewport } from '@angular/cdk/scrolling';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

const mockMeasures = [
  new Measure('m1', 'desc1'),
  new Measure('m2', 'desc2'),
  new Measure('m3', 'desc3'),
  new Measure('m4', 'desc4'),
];

class MockMeasuresService {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getMeasureList(datasetId: string): object {
    return of(mockMeasures);
  }
}

describe('PhenoMeasureSelectorBetaComponent', () => {
  let component: PhenoMeasureSelectorBetaComponent;
  let fixture: ComponentFixture<PhenoMeasureSelectorBetaComponent>;
  const mockDatasetsService = new MockDatasetsService();
  const mockMeasuresService = new MockMeasuresService();
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoMeasureSelectorBetaComponent],
      providers: [
        MeasuresService,
        {provide: MeasuresService, useValue: mockMeasuresService},
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''},
        provideHttpClientTesting(),
        CdkVirtualScrollViewport
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({}),
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    fixture = TestBed.createComponent(PhenoMeasureSelectorBetaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get ids of selected measures from state in person filters', () => {
    const mockState: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'range selector',
      roles: null
    };
    jest.spyOn(store, 'select').mockReturnValue(of([mockState]));
    component.ngOnInit();
    expect(component.selectedMeasureIds).toStrictEqual(['m1']);
  });

  it('should get ids of selected measures from state in famoly filters', () => {
    component.isFamilyFilters = true;
    const mockState1: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'range selector',
      roles: null
    };

    const mockState2: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm2',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null,
      roles: null
    };
    jest.spyOn(store, 'select').mockReturnValue(of([mockState1, mockState2]));
    component.ngOnInit();
    expect(component.selectedMeasureIds).toStrictEqual(['m1', 'm2']);
  });

  it('should check if measure is selected', () => {
    component.selectedMeasureIds = ['m1', 'm2'];

    expect(component.isMeasureSelected('m1')).toBe(true);
    expect(component.isMeasureSelected('m10')).toBe(false);
  });

  it('should close dropdown', () => {
    component.idxSubscription = new Subscription();
    component.showDropdown = true;
    component.selectedIdx = 10;
    component.topVisibleIdx = 8;
    component.closeDropdown();

    expect(component.idxSubscription).toBeNull();
    expect(component.showDropdown).toBe(false);
    expect(component.selectedIdx).toBe(-1);
    expect(component.topVisibleIdx).toBe(0);
  });

  it('should clear search field on clear button click', () => {
    component.searchString = 'searchValue';
    const loadDropdownDataSpy = jest.spyOn(component, 'loadDropdownData');
    component.selectedIdx = 10;
    component.topVisibleIdx = 8;

    component.onClearButtonClick();
    expect(component.searchString).toBe('');
    expect(loadDropdownDataSpy).toHaveBeenCalledWith();
    expect(component.selectedIdx).toBe(-1);
    expect(component.topVisibleIdx).toBe(0);
  });

  it('should clear search field on input field click', () => {
    const loadDropdownDataSpy = jest.spyOn(component, 'loadDropdownData');
    const selectMeasureSpy = jest.spyOn(component, 'selectMeasure');
    component.selectedIdx = 10;
    component.topVisibleIdx = 8;
    component.selectedMeasure = new Measure('m1', 'desc1');

    component.clear();
    expect(loadDropdownDataSpy).toHaveBeenCalledWith();
    expect(selectMeasureSpy).toHaveBeenCalledWith(null);
    expect(component.selectedIdx).toBe(-1);
    expect(component.topVisibleIdx).toBe(0);
  });

  it('should not clear search and reset dropdown when no measure selected', () => {
    const loadDropdownDataSpy = jest.spyOn(component, 'loadDropdownData');
    component.selectMeasure = null;
    component.clear();
    expect(loadDropdownDataSpy).not.toHaveBeenCalledWith();
  });

  it('should filter and load dropdown data', () => {
    component.loadingMeasures = false;
    component.measures = [
      new Measure('m1', 'desc1'),
      new Measure('otherMeasure', 'otherDesc'),
    ];
    component.searchString = 'm1';
    const event = new KeyboardEvent('keydown', {key: 'm'});
    component.loadDropdownData(event);

    expect(component.filteredMeasures).toStrictEqual([new Measure('m1', 'desc1')]);
  });

  it('should filter and load dropdown data after timeout', fakeAsync(() => {
    component.loadingMeasures = true;
    component.measures = [
      new Measure('m1', 'desc1'),
      new Measure('otherMeasure', 'otherDesc'),
    ];
    component.searchString = 'm1';
    const event = new KeyboardEvent('keydown', {key: 'm'});
    component.loadDropdownData(event);

    component.loadingMeasures = false;
    tick(500);

    expect(component.filteredMeasures).toStrictEqual([new Measure('m1', 'desc1')]);
  }));

  it('should not filter and load dropdown data if tab key is clicked', () => {
    component.measures = [
      new Measure('m1', 'desc1'),
      new Measure('otherMeasure', 'otherDesc'),
    ];
    component.searchString = 'm1';
    const event = new KeyboardEvent('keydown', {key: 'Tab'});
    component.loadDropdownData(event);

    expect(component.filteredMeasures).toStrictEqual([]);
  });

  it('should emit selected measure to parent', () => {
    const selectedMeasureChangeSpy = jest.spyOn(component.selectedMeasureChange, 'emit');
    const measure = new Measure('m5', 'desc5');
    component.searchString = 'm';

    component.selectMeasure(measure, true);
    expect(component.selectedMeasure).toBe(measure);
    expect(component.searchString).toBe('');
    expect(component.selectedMeasureIds).toStrictEqual(['m5']);
    expect(selectedMeasureChangeSpy).toHaveBeenCalledWith(measure);
  });

  it('should get new measures on changes', () => {
    const measuresChangeSpy = jest.spyOn(component.measuresChange, 'emit');
    component.measures = [];
    component.datasetId = 'datasetId';

    component.ngOnChanges();
    expect(component.measures).toStrictEqual(mockMeasures);
    expect(component.filteredMeasures).toStrictEqual(mockMeasures);
    expect(measuresChangeSpy).toHaveBeenCalledWith(mockMeasures);
  });
});
