import { HttpClientTestingModule } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';

import { PhenoMeasureSelectorComponent } from './pheno-measure-selector.component';
import {
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocomplete,
  MatAutocompleteOrigin,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { StoreModule } from '@ngrx/store';
import { ContinuousMeasure } from 'app/measures/measures';
import { of } from 'rxjs';

class MockDatasetsService {
  public getSelectedDataset(): object {
    return { id: 'testDataset' };
  }
}

const mockMeasures = [
  new ContinuousMeasure('m1', 1, 10),
  new ContinuousMeasure('m2', 0, 15),
  new ContinuousMeasure('m3', 2, 100),
  new ContinuousMeasure('m4', 5, 80),
];

class MockMeasuresService {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getContinuousMeasures(datasetId: string): object {
    return of(mockMeasures);
  }
}

describe('PhenoMeasureSelectorComponent', () => {
  let component: PhenoMeasureSelectorComponent;
  let fixture: ComponentFixture<PhenoMeasureSelectorComponent>;
  const mockDatasetsService = new MockDatasetsService();
  const mockMeasuresService = new MockMeasuresService();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [PhenoMeasureSelectorComponent],
      providers: [
        MeasuresService,
        {provide: MeasuresService, useValue: mockMeasuresService},
        ConfigService,
        {provide: DatasetsService, useValue: mockDatasetsService},
        UsersService,
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''}
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        StoreModule.forRoot({}),
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoMeasureSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load measures when changes are detected', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filterDataSpy = jest.spyOn(component as any, 'filterData');
    const measuresChangeEmitSpy = jest.spyOn(component.measuresChange, 'emit');
    component.datasetId = 'datasetId';
    component.measures = [];
    component.ngOnChanges();

    expect(component.measures).toStrictEqual(mockMeasures);
    expect(filterDataSpy).toHaveBeenCalledWith();
    expect(measuresChangeEmitSpy).toHaveBeenCalledWith(mockMeasures);
  });

  it('should handle tab keyboard event', () => {
    const prevItemSpy = jest.spyOn(component, 'prevItem').mockImplementation();
    const nextItemSpy = jest.spyOn(component, 'nextItem').mockImplementation();

    component.showDropdown = false;
    let event = new KeyboardEvent('keydown', {code: 'a'});
    component.handleTabKey(event);
    expect(prevItemSpy).not.toHaveBeenCalledWith();
    expect(nextItemSpy).not.toHaveBeenCalledWith();

    component.showDropdown = true;
    event = new KeyboardEvent('keydown', {code: 'a'});
    component.handleTabKey(event);
    expect(prevItemSpy).not.toHaveBeenCalledWith();
    expect(nextItemSpy).not.toHaveBeenCalledWith();

    component.showDropdown = true;
    event = new KeyboardEvent('keydown', {code: 'Tab'});
    component.handleTabKey(event);
    expect(prevItemSpy).not.toHaveBeenCalledWith();
    expect(nextItemSpy).toHaveBeenCalledWith();

    component.showDropdown = true;
    event = new KeyboardEvent('keydown', {code: 'Tab', shiftKey: true});
    component.handleTabKey(event);
    expect(prevItemSpy).toHaveBeenCalledTimes(1);
    expect(nextItemSpy).toHaveBeenCalledTimes(1);
  });

  it('should select measure', () => {
    const selectMeasureEmitSpy = jest.spyOn(component.selectedMeasureChange, 'emit');
    const measure = new ContinuousMeasure('m2', 0, 15);
    component.selectMeasure(measure);

    expect(component.selectedMeasure).toStrictEqual(measure);
    expect(component.searchString).toBe('m2');
    expect(selectMeasureEmitSpy).toHaveBeenCalledWith(measure);

    component.selectMeasure(null, false);

    expect(component.selectedMeasure).toBeNull();
    expect(component.searchString).toBe('');
    expect(selectMeasureEmitSpy).not.toHaveBeenCalledWith();
  });

  it('should reset when close dropdown', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const resetScrollSpy = jest.spyOn(component as any, 'resetScroll');
    const blurSpy = jest.spyOn(component['searchBox']['nativeElement'], 'blur');
    component.showDropdown = true;

    component.closeDropdown();
    expect(component.idxSubscription).toBeNull();
    expect(component.showDropdown).toBe(false);
    expect(resetScrollSpy).toHaveBeenCalledWith();
    expect(blurSpy).toHaveBeenCalledWith();
  });

  it('should clear on input click selected measure', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const resetScrollSpy = jest.spyOn(component as any, 'resetScroll');
    const loadDropdownDataSpy = jest.spyOn(component, 'loadDropdownData');
    const selectMeasureSpy = jest.spyOn(component, 'selectMeasure');
    component.selectedMeasure = new ContinuousMeasure('m2', 1, 100);

    component.clear();
    expect(resetScrollSpy).toHaveBeenCalledWith();
    expect(loadDropdownDataSpy).toHaveBeenCalledWith();
    expect(selectMeasureSpy).toHaveBeenCalledWith(null);
  });
  it('should not clear on input click selected measure when the measure is null', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const resetScrollSpy = jest.spyOn(component as any, 'resetScroll');
    const loadDropdownDataSpy = jest.spyOn(component, 'loadDropdownData');
    const selectMeasureSpy = jest.spyOn(component, 'selectMeasure');
    component.selectedMeasure = null;

    component.clear();
    expect(resetScrollSpy).not.toHaveBeenCalledWith();
    expect(loadDropdownDataSpy).not.toHaveBeenCalledWith();
    expect(selectMeasureSpy).not.toHaveBeenCalledWith();
  });

  it('should clear on clearing button click', () => {
    const loadDropdownDataSpy = jest.spyOn(component, 'loadDropdownData');
    const selectMeasureSpy = jest.spyOn(component, 'selectMeasure');
    component.searchString = 'search value';
    component.selectedMeasure = new ContinuousMeasure('m2', 1, 100);

    component.onClearButtonClick();
    expect(component.searchString).toBe('');
    expect(loadDropdownDataSpy).toHaveBeenCalledWith();
    expect(selectMeasureSpy).toHaveBeenCalledWith(null);
  });

  it('should trigger filter content when typing', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filterDataSpy = jest.spyOn(component as any, 'filterData');
    component.loadingMeasures = false;
    component.measures = mockMeasures;
    component.searchString = 'm1';
    const event = new KeyboardEvent('keyup', {key: '1'});

    component.loadDropdownData(event);

    expect(component.loadingMeasures).toBe(false);
    expect(filterDataSpy).toHaveBeenCalledWith();
    expect(component.filteredMeasures).toStrictEqual([mockMeasures[0]]);
  });

  it('should not trigger filtering content when pressing Tab', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const filterDataSpy = jest.spyOn(component as any, 'filterData');
    component.loadingMeasures = false;
    component.measures = mockMeasures;
    component.searchString = 'm1';
    const event = new KeyboardEvent('keyup', {key: 'Tab'});

    component.loadDropdownData(event);

    expect(component.loadingMeasures).toBe(false);
    expect(filterDataSpy).not.toHaveBeenCalledWith();
  });
});
