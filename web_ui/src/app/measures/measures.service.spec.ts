import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { MeasuresService } from './measures.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { of, lastValueFrom, take } from 'rxjs';
import { ContinuousMeasure, HistogramData } from './measures';
import { environment } from 'environments/environment';
import { Partitions } from 'app/gene-scores/gene-scores';

describe('MeasuresService', () => {
  let service: MeasuresService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [MeasuresService, ConfigService, provideHttpClient(), provideHttpClientTesting()],
      imports: [RouterTestingModule]
    });

    service = TestBed.inject(MeasuresService);
    jest.clearAllMocks();
  });
  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get continuous measures', async() => {
    const measures = [
      {measure: 'abc.subscale_v_inappropriate_speech', min: 0, max: 12},
      {measure: 'abc.total_score', min: 0, max: 138},
      {measure: 'abcl_18_59.adh_i_total', min: 0, max: 10}
    ];

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(measures));

    const response = await lastValueFrom(service.getContinuousMeasures('datasetId').pipe(take(1)));
    expect(httpGetSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'measures/type/continuous');
    expect(response).toStrictEqual([
      new ContinuousMeasure('abc.subscale_v_inappropriate_speech', 0, 12),
      new ContinuousMeasure('abc.total_score', 0, 138),
      new ContinuousMeasure('abcl_18_59.adh_i_total', 0, 10)
    ]);
  });


  it('should get measure histogram', async() => {
    const histogram = {
      measure: 'abc.subscale_ii_lethargy',
      desc: '',
      min: 0,
      max: 40,
      bars: [
        318,
        288,
        140,
      ],
      bins: [
        0,
        1.600000023841858,
        40
      ],
      step: 0.04
    };

    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(histogram));

    const response = await lastValueFrom(service.getMeasureHistogram('datasetId', 'measureName').pipe(take(1)));
    expect(httpPostSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'measures/histogram');
    expect(response).toStrictEqual(new HistogramData(
      [318, 288, 140],
      'abc.subscale_ii_lethargy',
      0,
      40,
      0.04,
      [0, 1.600000023841858, 40],
      ''
    ));
  });

  it('should get measure partitions', async() => {
    const partitions = {
      left: {
        count: 0,
        percent: 0
      },
      mid: {
        count: 14114,
        percent: 0.76
      },
      right: {
        count: 4345,
        percent: 0.23
      }
    };

    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(partitions));

    const response = await lastValueFrom(service.getMeasurePartitions('datasetId', 'measureName', 0, 10).pipe(take(1)));
    expect(httpPostSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'measures/partitions');
    expect(response).toStrictEqual(new Partitions(0, 0, 14114, 0.76, 4345, 0.23));
  });

  it('should get regressions', async() => {
    const regressions = {
      age: {
        display_name: 'age at assessment',
        instrument_name: 'pheno_common',
        measure_name: 'age_at_assessment'
      },
      iq: {
        display_name: 'nonverbal iq',
        instrument_name: 'ssc_core_descriptive',
        measure_name: 'ssc_diagnosis_nonverbal_iq'
      }
    };

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(regressions));

    const response = await lastValueFrom(service.getRegressions('datasetId').pipe(take(1)));
    expect(httpGetSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'measures/regressions');
    expect(response).toStrictEqual(regressions);
  });
});
