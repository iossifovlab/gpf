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
    regression_names: {}
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
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
