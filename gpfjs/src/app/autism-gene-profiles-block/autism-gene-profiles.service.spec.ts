import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ConfigService } from 'app/config/config.service';
// eslint-disable-next-line no-restricted-imports
import { lastValueFrom, of } from 'rxjs';
import { GeneProfilesService } from './autism-gene-profiles.service';
import { GeneProfilesSingleViewConfig, GeneProfilesGene } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { take } from 'rxjs/operators';

describe('GeneProfilesService', () => {
  let service: GeneProfilesService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ConfigService],
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(GeneProfilesService);
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
    expect(res).toBeInstanceOf(GeneProfilesSingleViewConfig);
  });

  it('should get single gene', async() => {
    const getGeneSpy = jest.spyOn(service['http'], 'get');
    getGeneSpy.mockReturnValue(of({ mockGeneProperty: 'mockGeneValue' }));

    const resultGene = service.getGene('geneMock1');

    expect(getGeneSpy).toHaveBeenCalledWith(service['config'].baseUrl + service['genesUrl'] + 'geneMock1');
    const res = await lastValueFrom(resultGene.pipe(take(1)));
    expect(res['mockGeneProperty']).toBe('mockGeneValue');
    expect(res).toBeInstanceOf(GeneProfilesGene);
  });
});
