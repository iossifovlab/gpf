import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';
import { take } from 'rxjs/operators';
import { AgpTableConfig } from './agp-table';
import { AgpTableService } from "./agp-table.service";


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

  it('should get config', () => {
    const getConfigSpy = spyOn(service['http'], 'get');
    getConfigSpy.and.returnValue(of({ mockConfigProperty: 'mockConfigValue' }));

    const resultConfig = service.getConfig();

    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    resultConfig.pipe(take(1)).subscribe(res => {
      expect(res['mockConfigProperty']).toEqual('mockConfigValue');
      expect(res).toBeInstanceOf(AgpTableConfig);
    });
  });

  it('should get genes', () => {
    const getGenesSpy = spyOn(service['http'], 'get');

    getGenesSpy.and.returnValue(of({}));
    service.getGenes(1);
    service.getGenes(1, 'mockSearch');
    service.getGenes(1, 'mockSearch', 'mockSort', 'desc');
    expect(getGenesSpy.calls.allArgs()).toEqual([
      [service['config'].baseUrl + service['genesUrl'] + '?page=1'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1' + '&symbol=mockSearch'],
      [service['config'].baseUrl + service['genesUrl'] + '?page=1' + '&symbol=mockSearch' + '&sortBy=mockSort&order=desc']
    ]);
  });
});
