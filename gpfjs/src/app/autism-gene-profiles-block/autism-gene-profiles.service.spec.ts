import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { AgpConfig, AgpGene } from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { take } from 'rxjs/operators';

describe('AutismGeneProfilesService', () => {
  let service: AutismGeneProfilesService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(AutismGeneProfilesService);
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
      expect(res).toBeInstanceOf(AgpConfig);
    });
  });

  it('should get single gene', () => {
    const getGeneSpy = spyOn(service['http'], 'get');
    getGeneSpy.and.returnValue(of({ mockGeneProperty: 'mockGeneValue' }));

    const resultGene = service.getGene('geneMock1');

    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'geneMock1');
    resultGene.pipe(take(1)).subscribe(res => {
      expect(res['mockGeneProperty']).toEqual('mockGeneValue');
      expect(res).toBeInstanceOf(AgpGene);
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

    getGenesSpy.and.returnValue(of([{ mockGeneOneProperty: 'mockGeneOneValue' }, { mockGeneTwoProperty: 'mockGeneTwoValue' }]));
    const resultGenes = service.getGenes(1);
    resultGenes.pipe(take(1)).subscribe(res => {
      expect(res[0]['mockGeneOneProperty']).toEqual('mockGeneOneValue');
      expect(res[0]).toBeInstanceOf(AgpGene);
      expect(res[1]['mockGeneTwoProperty']).toEqual('mockGeneTwoValue');
      expect(res[1]).toBeInstanceOf(AgpGene);
    });
  });
});
