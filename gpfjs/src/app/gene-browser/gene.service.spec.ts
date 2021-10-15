import { HttpClient } from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { environment } from 'environments/environment';
import { of } from 'rxjs/internal/observable/of';
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
    const geneFromJsonSpy = spyOn(Gene, 'fromJson');
    geneFromJsonSpy.and.returnValue('fakeGene' as any);
    const httpGetSpy = spyOn(HttpClient.prototype, 'get');
    httpGetSpy.and.returnValue(of('fakeResponse'));

    service.getGene('fakeSymbol').pipe(take(1)).subscribe((response) => {
      expect(response).toEqual('fakeGene' as any);
      expect(httpGetSpy.calls.allArgs()).toEqual([[
        environment.apiPath + 'genome/gene_models/default/' + 'fakeSymbol'
      ]]);
      expect(geneFromJsonSpy.calls.allArgs()).toEqual([['fakeResponse' as any]]);
    });
  });

  it('should search genes', () => {
    const httpGetSpy = spyOn(HttpClient.prototype, 'get');
    httpGetSpy.and.returnValue(of('fakeResponse'));

    service.searchGenes('fakeSearchTerm').pipe(take(1)).subscribe((response) => {
      expect(response).toEqual('fakeResponse' as any);
      expect(httpGetSpy.calls.allArgs()).toEqual([[
        environment.apiPath + 'genome/gene_models/search/' + 'FAKESEARCHTERM'
      ]]);
    });
  });
});
