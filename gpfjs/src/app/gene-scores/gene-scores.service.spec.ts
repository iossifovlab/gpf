import { APP_BASE_HREF } from '@angular/common';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { StoreModule } from '@ngrx/store';
import { ConfigService } from 'app/config/config.service';
import { GeneScoresService } from './gene-scores.service';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom, of, take } from 'rxjs';
import { CategoricalHistogram, GeneScore, NumberHistogram } from './gene-scores';

describe('GeneScoresService', () => {
  let service: GeneScoresService;
  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      imports: [StoreModule.forRoot({}), RouterTestingModule, HttpClientTestingModule],
      providers: [
        GeneScoresService,
        {provide: ConfigService, useValue: configMock},
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      declarations: [],
    }).compileComponents();
    jest.clearAllMocks();
    service = TestBed.inject(GeneScoresService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get scores with number histogram', async() => {
    const mockScore = {
      score: 'LGD_rank',
      desc: 'LGD rank - Gene rank after sorting by LGD vulnerability score',
      histogram: {
        config: {
          type: 'number',
          view_range: {
            min: 1,
            max: 18395
          },
          number_of_bins: 150,
          x_log_scale: false,
          y_log_scale: false,
          x_min_log: null
        },
        bins: [
          1,
          18272.373333333333,
          18395
        ],
        bars: [
          167,
          168
        ],
        out_of_range_bins: [
          0,
          0
        ],
        min_value: 1,
        max_value: 18394.5
      },
      help: 'Gene rank after sorting by LGD vulnerability score',
      small_values_desc: 'more likely to be vulnerable',
      large_values_desc: 'less likely to be vulnerable'
    };


    const mockScoreObject = new GeneScore(
      'LGD rank - Gene rank after sorting by LGD vulnerability score',
      'Gene rank after sorting by LGD vulnerability score',
      'LGD_rank',
      new NumberHistogram(
        [167, 168, 0],
        [1, 18272.373333333333, 18395],
        'less likely to be vulnerable',
        'more likely to be vulnerable',
        1,
        18395,
        false,
        false
      )
    );

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of([mockScore]));

    const response = await lastValueFrom(service.getGeneScores('LGD_rank').pipe(take(1)));

    expect(httpGetSpy.mock.calls[0][0]).toBe('testUrl/gene_scores/histograms?ids=LGD_rank');
    expect(response).toStrictEqual([mockScoreObject]);
  });

  it('should get scores with categorical histogram', async() => {
    const mockScore = {
      score: 'gene-score',
      desc: 'gene-score - Evidence strength supporting a gene\'s association with autism',
      histogram: {
        config: {
          type: 'categorical',
          value_order: [
            '1',
            '2',
            '3'
          ],
          y_log_scale: false
        },
        values: {
          1: 233,
          2: 706,
          3: 143
        }
      },
      help: 'Evidence strength supporting a gene\'s association with autism',
      small_values_desc: 'strong evidence for association with ASD',
      large_values_desc: 'weak evidence for association with ASD'
    };


    const mockScoreObject = new GeneScore(
      'gene-score - Evidence strength supporting a gene\'s association with autism',
      'Evidence strength supporting a gene\'s association with autism',
      'gene-score',
      new CategoricalHistogram(
        [
          { name: '1', value: 233 },
          { name: '2', value: 706 },
          { name: '3', value: 143 }
        ],
        ['1', '2', '3'],
        'weak evidence for association with ASD',
        'strong evidence for association with ASD',
        false
      )
    );

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of([mockScore]));

    const response = await lastValueFrom(service.getGeneScores('gene-score').pipe(take(1)));

    expect(httpGetSpy.mock.calls[0][0]).toBe('testUrl/gene_scores/histograms?ids=gene-score');
    expect(response).toStrictEqual([mockScoreObject]);
  });
});