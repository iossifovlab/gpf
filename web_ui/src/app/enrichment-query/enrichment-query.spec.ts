import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { of, lastValueFrom, take } from 'rxjs';
import { EnrichmentQueryService } from './enrichment-query.service';
import {
  ChildrenStats,
  EnrichmentEffectResult,
  EnrichmentResult,
  EnrichmentResults,
  EnrichmentTestResult
} from './enrichment-result';
import { BrowserQueryFilter, PersonSetCollection } from 'app/genotype-browser/genotype-browser';

const filterMock = {
  datasetId: 'SFARI_SSC_WGS_CSHL',
  enrichmentBackgroundModel: 'hg38/enrichment/ur_synonymous_SFARI_SSC_WGS_CSHL',
  enrichmentCountingModel: 'enrichment_events_counting',
  geneSet: {
    geneSet: 'autism candidates from Iossifov PNAS 2015',
    geneSetsCollection: 'autism',
    geneSetsTypes: []
  }
};

const resultMock = {
  selector: 'autism',
  peopleGroupId: 'phenotype',
  childrenStats: {
    M: 2057,
    F: 319,
    U: 0
  },
  LGDs: {
    all: {
      name: 'all',
      count: 632,
      overlapped: 31,
      expected: 24,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    },
    male: {
      name: 'male',
      count: 548,
      overlapped: 29,
      expected: 21,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    },
    female: {
      name: 'female',
      count: 84,
      overlapped: 2,
      expected: 3,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    }
  },
  missense: {
    all: {
      name: 'all',
      count: 632,
      overlapped: 31,
      expected: 24,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    },
    male: {
      name: 'male',
      count: 548,
      overlapped: 29,
      expected: 21,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    },
    female: {
      name: 'female',
      count: 84,
      overlapped: 2,
      expected: 3,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    }
  },
  synonymous: {
    all: {
      name: 'all',
      count: 632,
      overlapped: 31,
      expected: 24,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    },
    male: {
      name: 'male',
      count: 548,
      overlapped: 29,
      expected: 21,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    },
    female: {
      name: 'female',
      count: 84,
      overlapped: 2,
      expected: 3,
      pvalue: 1,
      countFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      },
      overlapFilter: {
        datasetId: 'SFARI_SSC_WGS_CSHL',
        effectTypes: [],
        gender: [],
        peopleGroup: {
          id: 'personSetCollectionId',
          checkedValues: []
        },
        studyTypes: [],
        variantTypes: []
      }
    }
  }
};

const enrichmentResults = new EnrichmentResults(
  'enrichmentDescription',
  [
    new EnrichmentResult(
      'autism',
      new EnrichmentEffectResult(
        new EnrichmentTestResult('all', 632, 24, 31, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        ),
        new EnrichmentTestResult('male', 548, 21, 29, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        ),
        new EnrichmentTestResult('female', 84, 3, 2, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        )
      ),
      new EnrichmentEffectResult(
        new EnrichmentTestResult('all', 632, 24, 31, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        ),
        new EnrichmentTestResult('male', 548, 21, 29, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        ),
        new EnrichmentTestResult('female', 84, 3, 2, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        )
      ),
      new EnrichmentEffectResult(
        new EnrichmentTestResult('all', 632, 24, 31, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        ),
        new EnrichmentTestResult('male', 548, 21, 29, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        ),
        new EnrichmentTestResult('female', 84, 3, 2, 1,
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
          new BrowserQueryFilter('SFARI_SSC_WGS_CSHL', undefined, [], [],
            new PersonSetCollection('personSetCollectionId', []), [], []),
        )
      ),
      new ChildrenStats(2057, 319, 0)
    )
  ]
);

describe('EnrichmentQueryService', () => {
  let service: EnrichmentQueryService;
  let configService: ConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        EnrichmentQueryService,
        ConfigService,
        provideHttpClient(),
        provideHttpClientTesting()],
      imports: []
    });

    service = TestBed.inject(EnrichmentQueryService);
    configService = TestBed.inject(ConfigService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get enrichment test', async() => {
    const enrichmentMock = {
      desc: 'enrichmentDescription',
      result: [resultMock]
    };

    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(enrichmentMock));

    const postResponse = service.getEnrichmentTest(filterMock);

    expect(httpPostSpy).toHaveBeenCalledWith(
      configService.baseUrl + 'enrichment/test',
      filterMock,
      expect.objectContaining({
        withCredentials: true,
      })
    );
    const res = await lastValueFrom(postResponse.pipe(take(1)));
    expect(res).toStrictEqual(enrichmentResults);
  });
});
