import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { lastValueFrom, of } from 'rxjs';
import { take } from 'rxjs/operators';
import { AgpTableConfig } from './autism-gene-profiles-table';
import { AgpTableService } from './autism-gene-profiles-table.service';

describe('AgpTableService', () => {
  let service: AgpTableService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(AgpTableService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get config', async() => {
    const getConfigSpy = jest.spyOn(service['http'], 'get');
    getConfigSpy.mockReturnValue(of({ mockConfigProperty: 'mockConfigValue' }));

    const resultConfig = service.getConfig();

    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    const res = await lastValueFrom(resultConfig.pipe(take(1)));
    expect(res['mockConfigProperty']).toBe('mockConfigValue');
    expect(res).toBeInstanceOf(AgpTableConfig);
  });

  it('should get genes', () => {
    const getGenesSpy = jest.spyOn(service['http'], 'get');

    getGenesSpy.mockReturnValue(of({}));
    service.getGenes(1);
    service.getGenes(1, 'mockSearch');
    service.getGenes(1, 'mockSearch', 'mockSort', 'desc');
    expect(getGenesSpy.mock.calls).toEqual([ // eslint-disable-line
      [service['config'].baseUrl + service['genesUrl'] + '?page=1'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1&symbol=mockSearch'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1&symbol=mockSearch&sortBy=mockSort&order=desc']
    ]);
  });
});
