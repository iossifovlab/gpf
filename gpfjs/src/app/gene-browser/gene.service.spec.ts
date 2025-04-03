import { HttpClient, provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
import { environment } from 'environments/environment';
import { lastValueFrom, of } from 'rxjs';
import { take } from 'rxjs/operators';
import { Gene } from './gene';
import { GeneService } from './gene.service';

describe('GeneService', () => {
  let service: GeneService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService, provideHttpClient()],
      imports: []
    });
    jest.clearAllMocks();
    service = TestBed.inject(GeneService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get gene', async() => {
    const geneFromJsonSpy = jest.spyOn(Gene, 'fromJson');
    geneFromJsonSpy.mockReturnValue('fakeGene' as any);
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    const response = await lastValueFrom(service.getGene('fakeSymbol').pipe(take(1)));
    expect(response).toBe('fakeGene' as any);
    expect(httpGetSpy.mock.calls[0][0]).toStrictEqual(environment.apiPath + 'genome/gene_models/default/fakeSymbol');
    expect(geneFromJsonSpy.mock.calls[0][0]).toBe('fakeResponse' as any);
  });

  it('should search genes', async() => {
    const httpGetSpy = jest.spyOn(HttpClient.prototype, 'get');
    httpGetSpy.mockReturnValue(of('fakeResponse'));

    const response = await lastValueFrom(service.searchGenes('fakeSearchTerm').pipe(take(1)));
    expect(response).toBe('fakeResponse' as any);
    expect(httpGetSpy.mock.calls[0][0]).toBe(
      environment.apiPath + 'genome/gene_models/search/fakeSearchTerm'
    );
  });

  it('should validate genes', async() => {
    const httpPostSpy = jest.spyOn(HttpClient.prototype, 'post');
    httpPostSpy.mockReturnValue(of(['invalidGene']));

    const genes = ['CHD8', 'POGZ', 'invalidGene'];
    const response = await lastValueFrom(service.validateGenes(genes).pipe(take(1)));
    expect(response).toStrictEqual(['invalidGene']);
    expect(httpPostSpy.mock.calls[0][0]).toBe(
      environment.apiPath + 'genome/gene_models/validate/'
    );
  });
});
