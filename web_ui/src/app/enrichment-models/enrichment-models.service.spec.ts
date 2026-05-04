// Import the necessary modules and dependencies
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { ConfigService } from '../config/config.service';
import { EnrichmentModelsService, EnrichmentModels } from './enrichment-models.service';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { of, lastValueFrom, take } from 'rxjs';
import { IdDescriptionName } from './iddescription';

describe('EnrichmentModelsService', () => {
  let service: EnrichmentModelsService;
  let httpMock: HttpTestingController;
  let configService: ConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [],
      providers: [EnrichmentModelsService, ConfigService, provideHttpClient(), provideHttpClientTesting()]
    });
    service = TestBed.inject(EnrichmentModelsService);
    httpMock = TestBed.inject(HttpTestingController);
    configService = TestBed.inject(ConfigService);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should get the background models for a given dataset id', async() => {
    const mockData = {
      counting: [
        { id: '1', name: 'Counting 1', desc: 'Description 1' },
        { id: '2', name: 'Counting 2', desc: 'Description 2' }
      ],
      background: [
        { id: '3', name: 'Background 1', desc: 'Description 3' },
        { id: '4', name: 'Background 2', desc: 'Description 4' }
      ],
      defaultCounting: '2',
      defaultBackground: '3'
    };

    const expectedResult: EnrichmentModels = {
      countings: [
        new IdDescriptionName('1', 'Description 1', 'Counting 1'),
        new IdDescriptionName('2', 'Description 2', 'Counting 2')
      ],
      backgrounds: [
        new IdDescriptionName('3', 'Description 3', 'Background 1'),
        new IdDescriptionName('4', 'Description 4', 'Background 2')
      ],
      defaultCounting: '2',
      defaultBackground: '3'
    };

    const mockDatasetId = 'test';
    const mockUrl = `${configService.baseUrl}enrichment/models/${mockDatasetId}`;

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of(mockData));

    const getResponse = service.getBackgroundModels(mockDatasetId);

    expect(httpGetSpy).toHaveBeenCalledWith(mockUrl);
    const res = await lastValueFrom(getResponse.pipe(take(1)));
    expect(res).toStrictEqual(expectedResult);
  });
});
