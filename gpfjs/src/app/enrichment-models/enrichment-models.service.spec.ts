// Import the necessary modules and dependencies
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ConfigService } from '../config/config.service';
import { EnrichmentModelsService, EnrichmentModels } from './enrichment-models.service';

describe('EnrichmentModelsService', () => {
  let service: EnrichmentModelsService;
  let httpMock: HttpTestingController;
  let configService: ConfigService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [EnrichmentModelsService, ConfigService]
    });
    service = TestBed.inject(EnrichmentModelsService);
    httpMock = TestBed.inject(HttpTestingController);
    configService = TestBed.inject(ConfigService);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should get the background models for a given dataset id', () => {
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
        { id: '1', name: 'Counting 1', description: 'Description 1' },
        { id: '2', name: 'Counting 2', description: 'Description 2' }
      ],
      backgrounds: [
        { id: '3', name: 'Background 1', description: 'Description 3' },
        { id: '4', name: 'Background 2', description: 'Description 4' }
      ],
      defaultCounting: '2',
      defaultBackground: '3'
    };

    const mockDatasetId = 'test';
    const mockUrl = `${configService.baseUrl}enrichment/models/${mockDatasetId}`;

    service.getBackgroundModels(mockDatasetId).subscribe((result: EnrichmentModels) => {
      expect(result).toStrictEqual(expectedResult);
    });

    const req = httpMock.expectOne(mockUrl);
    expect(req.request.method).toBe('GET');

    req.flush(mockData);
  });
});
