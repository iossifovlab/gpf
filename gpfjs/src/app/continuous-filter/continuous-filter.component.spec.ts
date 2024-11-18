import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { HistogramData } from 'app/measures/measures';
import { MeasuresService } from 'app/measures/measures.service';
import { Observable, of } from 'rxjs';

import { ContinuousFilterComponent } from './continuous-filter.component';
import { Store, StoreModule } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { PersonFilterState, ContinuousSelection, ContinuousFilterState } from 'app/person-filters/person-filters';
import { updateFamilyFilter, updatePersonFilter } from 'app/person-filters/person-filters.state';


const mockPersonAndFamilyFiltersState = {
  familyFilters: [
    new PersonFilterState(
      'familyName1',
      'continuous',
      'familyRole1',
      'familySource1',
      'familyFrom1',
      new ContinuousSelection(1, 2, 3, 4),
    ),
    new PersonFilterState(
      'familyName2',
      'continuous',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new ContinuousSelection(5, 6, 7, 8),
    )
  ],
  personFilters: [
    new PersonFilterState(
      'personName1',
      'continuous',
      'personRole1',
      'personSource1',
      'personFrom1',
      new ContinuousSelection(9, 10, 11, 12),
    ),
    new PersonFilterState(
      'personName2',
      'continuous',
      'personRole2',
      'personSource2',
      'personFrom2',
      new ContinuousSelection(13, 14, 15, 16),
    )
  ],
};

class MeasuresServiceMock {
  public getContinuousMeasures(): void {
    return null;
  }

  public getMeasureHistogram(datasetId: string, measureName: string): Observable<HistogramData> {
    return of(
      new HistogramData([], measureName, 0, 10, 3, [], 'description')
    );
  }

  public getRegressions(): void {
    return null;
  }
}

describe('ContinuousFilterComponent', () => {
  let component: ContinuousFilterComponent;
  let fixture: ComponentFixture<ContinuousFilterComponent>;
  const measuresServiceMock = new MeasuresServiceMock();
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [ContinuousFilterComponent],
      providers: [{provide: MeasuresService, useValue: measuresServiceMock}, ConfigService],
      imports: [HttpClientTestingModule, StoreModule.forRoot()]
    })
      .compileComponents();

    fixture = TestBed.createComponent(ContinuousFilterComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get family filters from state', () => {
    component.isFamilyFilters = true;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep(mockPersonAndFamilyFiltersState)));
    const filter = new ContinuousFilterState(
      'familyName2',
      'continuous',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new ContinuousSelection(5, 6, 7, 8),
    );
    component.continuousFilter = filter;
    component.ngOnInit();
    expect(component['continuousFilterState']).toStrictEqual(
      new PersonFilterState(
        'familyName2',
        'continuous',
        'familyRole2',
        'familySource2',
        'familyFrom2',
        new ContinuousSelection(5, 6, 7, 8),
      )
    );
  });

  it('should get person filters from state', () => {
    component.isFamilyFilters = false;
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep(mockPersonAndFamilyFiltersState)));
    const filter = new ContinuousFilterState(
      'personName2',
      'continuous',
      'personRole2',
      'personSource2',
      'personFrom2',
      new ContinuousSelection(13, 14, 15, 16),
    );
    component.continuousFilter = filter;
    component.ngOnInit();
    expect(component['continuousFilterState']).toStrictEqual(
      new PersonFilterState(
        'personName2',
        'continuous',
        'personRole2',
        'personSource2',
        'personFrom2',
        new ContinuousSelection(13, 14, 15, 16),
      ));
  });

  it('should use the filter passed by parent when family or person filters in state are null', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.isFamilyFilters = true;
    component.ngOnInit();
    expect(component['continuousFilterState']).toBeUndefined();

    component.isFamilyFilters = false;
    component.ngOnInit();
    expect(component['continuousFilterState']).toBeUndefined();
  });

  it('should get histogram data on changes', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.datasetId = 'datasetId';
    component.measureName = 'measureName';
    component['continuousFilterState'] = new PersonFilterState(
      'familyName2',
      'continuous',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new ContinuousSelection(null, null, 7, 8),
    );

    const getMeasureHistogramSpy = jest.spyOn(measuresServiceMock, 'getMeasureHistogram');
    component.ngOnChanges();

    expect(getMeasureHistogramSpy).toHaveBeenCalledWith('datasetId', 'measureName');
    expect(component.histogramData).toStrictEqual(new HistogramData([], 'measureName', 0, 10, 3, [], 'description'));
  });

  it('should set range start when working with family filters', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.isFamilyFilters = true;
    component.datasetId = 'datasetId';
    component.measureName = 'measureName';
    const filter = new PersonFilterState(
      'familyName2',
      'continuous',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new ContinuousSelection(5, 6, 7, 8),
    );
    component['continuousFilterState'] = filter;

    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const rangeChangesSpy = jest.spyOn(component['rangeChanges'], 'next');
    component.rangeStart = 50;

    expect(dispatchSpy).toHaveBeenCalledWith(updateFamilyFilter({familyFilter: cloneDeep(filter)}));
    expect(rangeChangesSpy).toHaveBeenCalledWith(['datasetId', 'measureName', 50, 6]);
  });

  it('should set range start when working with person filters', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.isFamilyFilters = false;
    component.datasetId = 'datasetId';
    component.measureName = 'measureName';
    const filter = new PersonFilterState(
      'personName1',
      'continuous',
      'personRole1',
      'personSource1',
      'personFrom1',
      new ContinuousSelection(9, 10, 11, 12),
    );
    component['continuousFilterState'] = filter;

    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const rangeChangesSpy = jest.spyOn(component['rangeChanges'], 'next');
    component.rangeStart = 40;

    expect(dispatchSpy).toHaveBeenCalledWith(updatePersonFilter({personFilter: cloneDeep(filter)}));
    expect(rangeChangesSpy).toHaveBeenCalledWith(['datasetId', 'measureName', 40, 10]);
  });

  it('should get range start', () => {
    const filter = new PersonFilterState(
      'personName1',
      'continuous',
      'personRole1',
      'personSource1',
      'personFrom1',
      new ContinuousSelection(9, 10, 11, 12),
    );
    component['continuousFilterState'] = filter;

    expect(component.rangeStart).toBe(9);
  });

  it('should set range end when working with family filters', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.isFamilyFilters = true;
    component.datasetId = 'datasetId';
    component.measureName = 'measureName';
    const filter = new PersonFilterState(
      'familyName2',
      'continuous',
      'familyRole2',
      'familySource2',
      'familyFrom2',
      new ContinuousSelection(5, 6, 7, 8),
    );
    component['continuousFilterState'] = filter;

    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const rangeChangesSpy = jest.spyOn(component['rangeChanges'], 'next');
    component.rangeEnd = 50;

    expect(dispatchSpy).toHaveBeenCalledWith(updateFamilyFilter({familyFilter: cloneDeep(filter)}));
    expect(rangeChangesSpy).toHaveBeenCalledWith(['datasetId', 'measureName', 5, 50]);
  });

  it('should set range end when working with person filters', () => {
    jest.spyOn(store, 'select').mockReturnValue(of(cloneDeep({
      familyFilters: null,
      personFilters: null
    })));

    component.isFamilyFilters = false;
    component.datasetId = 'datasetId';
    component.measureName = 'measureName';
    const filter = new PersonFilterState(
      'personName1',
      'continuous',
      'personRole1',
      'personSource1',
      'personFrom1',
      new ContinuousSelection(9, 10, 11, 12),
    );
    component['continuousFilterState'] = filter;

    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const rangeChangesSpy = jest.spyOn(component['rangeChanges'], 'next');
    component.rangeEnd = 40;

    expect(dispatchSpy).toHaveBeenCalledWith(updatePersonFilter({personFilter: cloneDeep(filter)}));
    expect(rangeChangesSpy).toHaveBeenCalledWith(['datasetId', 'measureName', 9, 40]);
  });

  it('should get range end', () => {
    const filter = new PersonFilterState(
      'personName1',
      'continuous',
      'personRole1',
      'personSource1',
      'personFrom1',
      new ContinuousSelection(9, 10, 11, 12),
    );
    component['continuousFilterState'] = filter;

    expect(component.rangeEnd).toBe(10);
  });
});
