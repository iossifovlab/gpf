import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { of } from 'rxjs';
import { GeneSet } from './gene-sets';
import { GeneSetsService } from './gene-sets.service';

describe('GeneSetsService', () => {
  let service: GeneSetsService;

  beforeEach(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      providers: [{provide: ConfigService, useValue: configMock}, HttpClientTestingModule, GeneSetsService],
      imports: [HttpClientTestingModule],
    });

    service = TestBed.inject(GeneSetsService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should getGeneSetsCollections', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));
    service.getGeneSetsCollections();

    expect(httpGetSpy.mock.calls).toEqual(
      [
        [
          'testUrl/gene_sets/gene_sets_collections',
          { headers: {'Content-Type': 'application/json'}, withCredentials: true }
        ]
      ]
    );
  });

  it('should downloadGeneSet', () => {
    const mockGeneSet: GeneSet = {
      count: 111,
      desc: 'list of genes description',
      download: 'gene_sets/gene_set_download?geneSetsCollection=autism&geneSet=List+of+genes&geneSetsTypes=%7B%7D',
      name: 'List of genes'
    };

    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));
    service.downloadGeneSet(mockGeneSet);

    expect(httpGetSpy.mock.calls).toEqual(
      [
        [
          'testUrl/gene_sets/gene_sets_collections',
          {headers: {'Content-Type': 'application/json'}, withCredentials: true}
        ],
        [
          'testUrl/gene_sets/gene_set_download?geneSetsCollection=autism&geneSet=List+of+genes&geneSetsTypes=%7B%7D',
          {observe: 'response', responseType: 'blob'}
        ]
      ]
    );
  });
});
