import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { environment } from 'environments/environment';
import { of } from 'rxjs';
import { take } from 'rxjs/operators';
import { Gene } from './gene';
import { GeneService } from './gene.service';

describe('GeneService', () => {
  let service: GeneService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [
        HttpClientTestingModule,
      ]
    });
    service = TestBed.inject(GeneService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get gene', () => {
    const geneFromJsonSpy = jest.spyOn(Gene, 'fromJson');
    geneFromJsonSpy.mockReturnValue('fakeGene' as any);
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    service.getGene('fakeSymbol').pipe(take(1)).subscribe((response) => {
      expect(response).toEqual('fakeGene' as any);
      expect(httpGetSpy.mock.calls).toEqual([[
        environment.apiPath + 'genome/gene_models/default/fakeSymbol'
      ]]);
      expect(geneFromJsonSpy.mock.calls).toEqual([['fakeResponse' as any]]);
    });
  });

  it('should search genes', () => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    service.searchGenes('fakeSearchTerm').pipe(take(1)).subscribe((response) => {
      expect(response).toEqual('fakeResponse' as any);
      expect(httpGetSpy.mock.calls).toEqual([[
        environment.apiPath + 'genome/gene_models/search/FAKESEARCHTERM'
      ]]);
    });
  });
});
