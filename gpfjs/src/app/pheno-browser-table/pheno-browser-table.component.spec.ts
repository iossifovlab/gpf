import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { PhenoBrowserTableComponent } from './pheno-browser-table.component';
import { NumberWithExpPipe } from '../utils/number-with-exp.pipe';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';
import { ResizeService } from '../table/resize.service';
import { GetRegressionIdsPipe } from 'app/utils/get-regression-ids.pipe';
import { PhenoMeasures } from 'app/pheno-browser/pheno-browser';
import { cloneDeep } from 'lodash';


const mockMeasures = PhenoMeasures.fromJson(
  {
    /* eslint-disable */
    base_image_url: '',
    measures: [{
        Index: 1,
        instrument_name: 'abc',
        values_domain: '0,1',
        figure_distribution: 'test.jpg',
        figure_distribution_small: null,
        measure_id: 'abc.a',
        measure_name: 'a',
        measure_type: 'abc',
        description: 'a test measure',
        regressions: [{
            regression_id: 'age',
            measure_id: 'abc.a',
            figure_regression: 'imagepathage',
            figure_regression_small: 'imagepathagesmall',
            pvalue_regression_male: 0.01,
            pvalue_regression_female: 1.0,
          },
          {
            regression_id: 'iq',
            measure_id: 'abc.a',
            figure_regression: 'imagepathiq',
            figure_regression_small: 'imagepathiqsmall',
            pvalue_regression_male: 0.02,
            pvalue_regression_female: 2.0,
        }]
      }, {
        Index: 2,
        instrument_name: 'bca',
        values_domain: '0,1',
        figure_distribution: 'test.jpg',
        figure_distribution_small: null,
        measure_id: 'bca.b',
        measure_name: 'b',
        measure_type: 'bca',
        description: 'b test measure',
        regressions: [{
            regression_id: 'age',
            measure_id: 'bca.b',
            figure_regression: 'imagepathage',
            figure_regression_small: 'imagepathagesmall',
            pvalue_regression_male: 0.03,
            pvalue_regression_female: 3.0,
        }]
      }, {
        Index: 3,
        instrument_name: 'cab',
        values_domain: '0,1',
        figure_distribution: 'test.jpg',
        figure_distribution_small: null,
        measure_id: 'cab.c',
        measure_name: 'c',
        measure_type: 'cab',
        description: 'c test measure',
        regressions: [{
            regression_id: 'iq',
            measure_id: 'cab.c',
            figure_regression: 'imagepathiq',
            figure_regression_small: 'imagepathiqsmall',
            pvalue_regression_male: 0.04,
            pvalue_regression_female: 4.0,
        }],
      }
    ],
    has_descriptions: true,
    regression_names: {age: 'age at assessment', iq: 'nonverbal iq'}
    /* eslint-enable */
  }
);

describe('PhenoBrowserTableComponent; no regressions', () => {
  let component: PhenoBrowserTableComponent;
  let fixture: ComponentFixture<PhenoBrowserTableComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [NgbModule],
      declarations: [
        PhenoBrowserTableComponent,
        PhenoBrowserTableComponent,
        NumberWithExpPipe,
        GetRegressionIdsPipe
      ],
      providers: [
        { provide: PValueIntensityPipe, useClass: PValueIntensityPipe },
        { provide: ResizeService, useClass: ResizeService },
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoBrowserTableComponent);
    component = fixture.componentInstance;
    component.measures = cloneDeep(mockMeasures);
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should sort table by insturment', () => {
    const data = cloneDeep(mockMeasures.measures);
    component.sortTable(data, 'desc', 'instrumentName');
    expect(data[0].instrumentName).toBe('cab');
    expect(data[1].instrumentName).toBe('bca');
    expect(data[2].instrumentName).toBe('abc');
  });

  it('should sort table by pheno measure', () => {
    const data = cloneDeep(mockMeasures.measures);
    component.sortTable(data, 'desc', 'measureName');
    expect(data[0].measureName).toBe('c');
    expect(data[1].measureName).toBe('b');
    expect(data[2].measureName).toBe('a');
  });

  it('should sort table by measure type', () => {
    const data = cloneDeep(mockMeasures.measures);
    component.sortTable(data, 'desc', 'measureType');
    expect(data[0].measureType).toBe('cab');
    expect(data[1].measureType).toBe('bca');
    expect(data[2].measureType).toBe('abc');
  });

  it('should sort table by male regression', () => {
    const data = cloneDeep(mockMeasures.measures);
    component.sortTable(data, 'desc', 'iq.pvalueRegressionMale');
    expect(data[0].regressions.getReg('iq').pvalueRegressionMale).toBe(0.04);
    expect(data[1].regressions.getReg('iq').pvalueRegressionMale).toBe(0.02);
    expect(data[2].regressions.getReg('iq').pvalueRegressionMale).toBeNull();
  });

  it('should sort table by female regression', () => {
    const data = cloneDeep(mockMeasures.measures);
    component.sortTable(data, 'asc', 'age.pvalueRegressionFemale');
    expect(data[0].regressions.getReg('age').pvalueRegressionFemale).toBeNull();
    expect(data[1].regressions.getReg('age').pvalueRegressionFemale).toBe(1);
    expect(data[2].regressions.getReg('age').pvalueRegressionFemale).toBe(3);
  });

  it('should sort when there is regression value NaN', () => {
    const data = cloneDeep(mockMeasures.measures);
    data[0].regressions.getReg('age').pvalueRegressionFemale = NaN;
    component.sortTable(data, 'asc', 'age.pvalueRegressionFemale');
    expect(data[0].regressions.getReg('age').pvalueRegressionFemale).toBeNull();
    expect(data[1].regressions.getReg('age').pvalueRegressionFemale).toBeNaN();
    expect(data[2].regressions.getReg('age').pvalueRegressionFemale).toBe(3);
  });

  it('should sort when there is regression value undefined', () => {
    const data = cloneDeep(mockMeasures.measures);
    data[1].regressions.getReg('age').pvalueRegressionFemale = undefined;
    component.sortTable(data, 'asc', 'age.pvalueRegressionFemale');
    expect(data[0].regressions.getReg('age').pvalueRegressionFemale).toBeUndefined();
    expect(data[1].regressions.getReg('age').pvalueRegressionFemale).toBeNull();
    expect(data[2].regressions.getReg('age').pvalueRegressionFemale).toBe(1);
  });

  it('should count columns', () => {
    expect(component.columnsCount).toBe(4);
    const resizeSpy = jest.spyOn(component, 'onResize');
    component.ngOnInit();
    expect(component.columnsCount).toBe(9);
    expect(resizeSpy).toHaveBeenCalledWith();
  });
});
