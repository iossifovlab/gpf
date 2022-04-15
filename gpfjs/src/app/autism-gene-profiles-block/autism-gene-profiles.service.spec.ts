import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';
import { AutismGeneProfilesService } from './autism-gene-profiles.service';
import { AgpSingleViewConfig, AgpGene } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
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
    const getConfigSpy = jest.spyOn(service['http'], 'get');
    getConfigSpy.mockReturnValue(of({ mockConfigProperty: 'mockConfigValue' }));

    const resultConfig = service.getConfig();

    expect(getConfigSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['configUrl']);
    resultConfig.pipe(take(1)).subscribe(res => {
      expect(res['mockConfigProperty']).toEqual('mockConfigValue');
      expect(res).toBeInstanceOf(AgpSingleViewConfig);
    });
  });

  it('should get single gene', () => {
    const getGeneSpy = jest.spyOn(service['http'], 'get');
    getGeneSpy.mockReturnValue(of({ mockGeneProperty: 'mockGeneValue' }));

    const resultGene = service.getGene('geneMock1');

    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'geneMock1');
    resultGene.pipe(take(1)).subscribe(res => {
      expect(res['mockGeneProperty']).toEqual('mockGeneValue');
      expect(res).toBeInstanceOf(AgpGene);
    });
  });
});
