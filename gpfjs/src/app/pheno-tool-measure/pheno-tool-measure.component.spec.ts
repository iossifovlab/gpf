import { HttpClient, HttpHandler } from '@angular/common/http';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { MeasuresService } from 'app/measures/measures.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';

import { PhenoToolMeasureComponent } from './pheno-tool-measure.component';
import { Observable, of } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Store, StoreModule } from '@ngrx/store';
import { phenoToolMeasureReducer } from './pheno-tool-measure.state';
import { ContinuousMeasure } from 'app/measures/measures';
import { Dataset, GeneBrowser } from 'app/datasets/datasets';

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
  null,
  null,
  null,
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  true
);

const regressionMock = {
  age: {
    display_name: 'age at assessment',
    instrument_name: 'pheno_common',
    measure_name: 'age_at_assessment'
  }
};

class DatasetsServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getDataset(datasetId: string): Observable<Dataset> {
    return of(datasetMock);
  }
}

class MeasuresServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getRegressions(datasetId: string): Observable<object> {
    return of(regressionMock);
  }
}

describe('PhenoToolMeasureComponent', () => {
  let component: PhenoToolMeasureComponent;
  let fixture: ComponentFixture<PhenoToolMeasureComponent>;
  let store: Store;
  const measuresServiceMock = new MeasuresServiceMock();
  const datasetsServiceMock = new DatasetsServiceMock();

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolMeasureComponent,
      ],
      providers: [
        MeasuresService,
        HttpClient,
        HttpHandler,
        ConfigService,
        UsersService,
        { provide: DatasetsService, useValue: datasetsServiceMock },
        { provide: MeasuresService, useValue: measuresServiceMock },
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [RouterTestingModule, StoreModule.forRoot({phenoToolMeasure: phenoToolMeasureReducer})],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolMeasureComponent);
    component = fixture.componentInstance;

    const selectedDatasetMockModel = {selectedDatasetId: 'testId'};

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of(selectedDatasetMockModel));
    jest.spyOn(store, 'dispatch').mockReturnValue(null);

    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get regressions and selected dataset', () => {
    component.ngOnInit();
    expect(component.dataset).toStrictEqual(datasetMock);
    expect(component.regressions).toStrictEqual(regressionMock);
    expect(component.regressionNames).toStrictEqual(['age']);
  });

  it('should set measure', () => {
    const updateStateSpy = jest.spyOn(component, 'updateState');
    component.normalizeBy = [
      {
        display_name: 'd1',
        instrument_name: 'i1',
        measure_name: 'm1'
      },
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      }
    ];
    component.measure = new ContinuousMeasure('i1.m1', 0, 10);
    expect(component.normalizeBy).toStrictEqual([{
      display_name: 'd2',
      instrument_name: 'i2',
      measure_name: 'm2'
    }]);
    expect(component.selectedMeasure).toStrictEqual(new ContinuousMeasure('i1.m1', 0, 10));
    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should get measure', () => {
    component.selectedMeasure = new ContinuousMeasure('i1.m1', 0, 10);
    expect(component.measure).toStrictEqual(new ContinuousMeasure('i1.m1', 0, 10));
  });

  it('should check normalize by', () => {
    const updateStateSpy = jest.spyOn(component, 'updateState');
    component.normalizeBy = [
      {
        display_name: 'd1',
        instrument_name: 'i1',
        measure_name: 'm1'
      },
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      }
    ];
    const mockCheckEvent = {
      target: {
        checked: true
      }
    };

    component.onNormalizeByChange({
      display_name: 'd1',
      instrument_name: 'i1',
      measure_name: 'm1'
    }, mockCheckEvent);
    expect(component.normalizeBy).toStrictEqual([
      {
        display_name: 'd1',
        instrument_name: 'i1',
        measure_name: 'm1'
      },
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      }
    ]);

    expect(updateStateSpy).toHaveBeenCalledWith();

    component.onNormalizeByChange({
      display_name: 'd3',
      instrument_name: 'i3',
      measure_name: 'm3'
    }, mockCheckEvent);
    expect(component.normalizeBy).toStrictEqual([
      {
        display_name: 'd1',
        instrument_name: 'i1',
        measure_name: 'm1'
      },
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      },
      {
        display_name: 'd3',
        instrument_name: 'i3',
        measure_name: 'm3'
      }
    ]);
  });

  it('should uncheck normalize by', () => {
    const updateStateSpy = jest.spyOn(component, 'updateState');
    component.normalizeBy = [
      {
        display_name: 'd1',
        instrument_name: 'i1',
        measure_name: 'm1'
      },
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      }
    ];
    const mockCheckEvent = {
      target: {
        checked: false
      }
    };

    component.onNormalizeByChange({
      display_name: 'd1',
      instrument_name: 'i1',
      measure_name: 'm1'
    }, mockCheckEvent);
    expect(component.normalizeBy).toStrictEqual([
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      }
    ]);

    expect(updateStateSpy).toHaveBeenCalledWith();
  });

  it('should check if measure is normalized by', () => {
    component.normalizeBy = [
      {
        display_name: 'd1',
        instrument_name: 'i1',
        measure_name: 'm1'
      },
      {
        display_name: 'd2',
        instrument_name: 'i2',
        measure_name: 'm2'
      }
    ];

    expect(component.isNormalizedBy('m1')).toBe(true);
    expect(component.isNormalizedBy('m111')).toBe(false);
  });
});
