import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonFiltersSelectorComponent } from './person-filters-selector.component';
import { Store, StoreModule } from '@ngrx/store';
import { MeasuresService } from 'app/measures/measures.service';
import { provideHttpClient } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import {
  Column,
  Dataset,
  GeneBrowser,
  GenotypeBrowser,
  PersonFilter,
  PersonSet,
  PersonSetCollection,
  PersonSetCollections
} from 'app/datasets/datasets';
import { UserGroup } from 'app/users-groups/users-groups';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Observable, of } from 'rxjs';
import {
  MeasureHistogramState,
  setFamilyMeasureHistogramsCategorical,
  setFamilyMeasureHistogramsContinuous,
  setPersonMeasureHistogramsCategorical,
  setPersonMeasureHistogramsContinuous
} from './measure-histogram.state';
import { Measure, MeasureHistogram } from 'app/measures/measures';
import { CategoricalHistogram, NumberHistogram } from 'app/utils/histogram-types';
import { resetErrors, setErrors } from 'app/common/errors.state';

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

const measureHistogramMock = new MeasureHistogram(
  'm1',
  new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 5, 10, true, true),
  'desc'
);

const measureHistogramMock2 = new MeasureHistogram(
  'm2',
  new NumberHistogram([1, 2], [4, 5], 'larger1', 'smaller1', 5, 10, true, true),
  'desc2'
);

const measureHistogramMock3 = new MeasureHistogram(
  'm3',
  new CategoricalHistogram(
    [
      {name: 'name1', value: 10},
      {name: 'name2', value: 20},
      {name: 'name3', value: 30},
      {name: 'name4', value: 40},
      {name: 'name5', value: 50},
    ],
    ['name1', 'name2', 'name3', 'name4', 'name5'],
    'large value descriptions',
    'small value descriptions',
    true,
    0,
    30
  ),
  'desc3'
);

class MeasuresServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getMeasureHistogramBeta(datasetId: string, measure: string): Observable<MeasureHistogram> {
    if (measure === 'm1') {
      return of(measureHistogramMock);
    } else if (measure === 'm2') {
      return of(measureHistogramMock2);
    } else if (measure === 'm3') {
      return of(measureHistogramMock3);
    }
  }
}

describe('PersonFiltersSelectorComponent', () => {
  let component: PersonFiltersSelectorComponent;
  let fixture: ComponentFixture<PersonFiltersSelectorComponent>;
  let store: Store;
  const measuresServiceMock = new MeasuresServiceMock();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [PersonFiltersSelectorComponent],
      imports: [StoreModule.forRoot()],
      providers: [
        ConfigService,
        provideHttpClient(),
        { provide: MeasuresService, useValue: measuresServiceMock}
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);

    fixture = TestBed.createComponent(PersonFiltersSelectorComponent);
    component = fixture.componentInstance;

    component.dataset = datasetMock;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should select family filters measure histograms from state and get histograms', () => {
    component.isFamilyFilters = true;

    const mockState: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'range selector'
    };
    jest.spyOn(store, 'select').mockReturnValue(of([mockState]));

    component.ngOnInit();
    expect(component.areFiltersSelected).toBe(true);
    expect(component.selectedMeasureHistograms).toStrictEqual([{
      measureHistogram: measureHistogramMock,
      state: mockState
    }]);
  });

  it('should select person filters measure histograms from state', () => {
    const mockState: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm1',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2'],
      categoricalView: 'range selector'
    };
    jest.spyOn(store, 'select').mockReturnValue(of([mockState]));

    component.ngOnInit();
    expect(component.areFiltersSelected).toBe(true);
  });

  it('should reset validation errors on component destruction in family filters', () => {
    component.isFamilyFilters = true;
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.ngOnDestroy();
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({ componentId: 'familyFilters' }));
  });

  it('should reset validation errors on component destruction in person filters', () => {
    component.isFamilyFilters = false;
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    component.ngOnDestroy();
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({ componentId: 'personFilters' }));
  });

  it('should add measure with continuous histogram in family filters', () => {
    component.isFamilyFilters = true;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const defaultState = {
      histogramType: 'continuous',
      measure: 'm2',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    const measure = new Measure('m2', 'desc2');

    component.addMeasure(measure);
    expect(component.selectedMeasureHistograms).toStrictEqual([{
      measureHistogram: measureHistogramMock2,
      state: defaultState
    }]);
    expect(dispatchSpy).toHaveBeenCalledWith(setFamilyMeasureHistogramsContinuous(
      {
        measure: 'm2',
        rangeStart: 5,
        rangeEnd: 10
      }
    ));
  });

  it('should add measure with continuous histogram in person filters', () => {
    component.isFamilyFilters = false;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const defaultState = {
      histogramType: 'continuous',
      measure: 'm2',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    const measure = new Measure('m2', 'desc2');

    component.addMeasure(measure);
    expect(component.selectedMeasureHistograms).toStrictEqual([{
      measureHistogram: measureHistogramMock2,
      state: defaultState
    }]);
    expect(dispatchSpy).toHaveBeenCalledWith(setPersonMeasureHistogramsContinuous(
      {
        measure: 'm2',
        rangeStart: 5,
        rangeEnd: 10
      }
    ));
  });

  it('should add measure with categorical histogram in family filters', () => {
    component.selectedMeasureHistograms = [];
    component.isFamilyFilters = true;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const defaultState = {
      histogramType: 'categorical',
      measure: 'm3',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2', 'name3', 'name4', 'name5'],
      categoricalView: 'range selector'
    };
    const measure = new Measure('m3', 'desc3');

    component.addMeasure(measure);
    expect(component.selectedMeasureHistograms).toStrictEqual([{
      measureHistogram: measureHistogramMock3,
      state: defaultState
    }]);
    expect(dispatchSpy).toHaveBeenCalledWith(setFamilyMeasureHistogramsCategorical(
      {
        measure: 'm3',
        values: ['name1', 'name2', 'name3', 'name4', 'name5'],
        categoricalView: 'range selector'
      }
    ));
  });

  it('should add measure with categorical histogram in person filters', () => {
    component.selectedMeasureHistograms = [];
    component.isFamilyFilters = false;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const defaultState = {
      histogramType: 'categorical',
      measure: 'm3',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2', 'name3', 'name4', 'name5'],
      categoricalView: 'range selector'
    };
    const measure = new Measure('m3', 'desc3');

    component.addMeasure(measure);
    expect(component.selectedMeasureHistograms).toStrictEqual([{
      measureHistogram: measureHistogramMock3,
      state: defaultState
    }]);
    expect(dispatchSpy).toHaveBeenCalledWith(setPersonMeasureHistogramsCategorical(
      {
        measure: 'm3',
        values: ['name1', 'name2', 'name3', 'name4', 'name5'],
        categoricalView: 'range selector'
      }
    ));
  });

  it('should save continuous measure state to state in family filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    const mockState: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };

    component.isFamilyFilters = true;
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(setFamilyMeasureHistogramsContinuous({
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10
    }));
  });

  it('should save continuous measure state to state in person filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    const mockState: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };

    component.isFamilyFilters = false;
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(setPersonMeasureHistogramsContinuous({
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10
    }));
  });

  it('should save categorical measure state to state in family filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    const mockState: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm3',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2'],
      categoricalView: 'click selector'
    };

    component.isFamilyFilters = true;
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(setFamilyMeasureHistogramsCategorical({
      measure: 'm3',
      values: ['name1', 'name2'],
      categoricalView: 'click selector'
    }));
  });

  it('should save categorical measure state to state in person filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();
    const mockState: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm3',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2'],
      categoricalView: 'click selector'
    };

    component.isFamilyFilters = false;
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(setPersonMeasureHistogramsCategorical({
      measure: 'm3',
      values: ['name1', 'name2'],
      categoricalView: 'click selector'
    }));
  });

  it('should remove measure from state and reset error in family filters', () => {
    component.isFamilyFilters = true;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const mockState1: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm3',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2'],
      categoricalView: 'click selector'
    };
    const hist1: {measureHistogram: MeasureHistogram, state: MeasureHistogramState} = {
      measureHistogram: measureHistogramMock3,
      state: mockState1
    };

    const mockState2: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm2',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    const hist2: {measureHistogram: MeasureHistogram, state: MeasureHistogramState} = {
      measureHistogram: measureHistogramMock3,
      state: mockState2
    };
    component.selectedMeasureHistograms.push(hist1, hist2);
    component.removeFromState('m3');
    expect(component.selectedMeasureHistograms).toStrictEqual([hist2]);
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({componentId: 'familyFilters: m3'}));
  });

  it('should remove measure from state and reset errors in person filters', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const mockState1: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm3',
      rangeStart: null,
      rangeEnd: null,
      values: ['name1', 'name2'],
      categoricalView: 'click selector'
    };
    const hist1: {measureHistogram: MeasureHistogram, state: MeasureHistogramState} = {
      measureHistogram: measureHistogramMock3,
      state: mockState1
    };

    const mockState2: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm2',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    const hist2: {measureHistogram: MeasureHistogram, state: MeasureHistogramState} = {
      measureHistogram: measureHistogramMock3,
      state: mockState2
    };
    component.selectedMeasureHistograms.push(hist1, hist2);
    component.removeFromState('m3');
    expect(component.selectedMeasureHistograms).toStrictEqual([hist2]);
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({componentId: 'personFilters: m3'}));
  });

  it('should validate selected measure in family filters', () => {
    component.isFamilyFilters = true;
    component.areFiltersSelected = false;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const mockState: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'familyFilters', errors: ['Select a measure.']
      }
    }));
  });

  it('should validate selected measure in person filters', () => {
    component.isFamilyFilters = false;
    component.areFiltersSelected = false;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const mockState: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(setErrors({
      errors: {
        componentId: 'personFilters', errors: ['Select a measure.']
      }
    }));
  });

  it('should reset validation errors when validation is successful', () => {
    component.isFamilyFilters = false;
    component.areFiltersSelected = true;
    const dispatchSpy = jest.spyOn(store, 'dispatch').mockImplementation();

    const mockState: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm1',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null
    };
    component.addToState(mockState);
    expect(dispatchSpy).toHaveBeenCalledWith(resetErrors({ componentId: 'personFilters'}));
  });
});
