import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { DomainRange } from 'app/gene-view/gene';
import { QueryStateCollector } from 'app/query/query-state-provider';
import { QueryService } from 'app/query/query.service';
import { StateRestoreService } from 'app/store/state-restore.service';
import { UsersService } from 'app/users/users.service';
import { of } from 'rxjs/internal/observable/of';
import { GeneBrowserComponent } from './gene-browser.component';

class MockActivatedRoute {
  params = {dataset: 'testDatasetId', get: () => ''};
  parent = {params: of(this.params)};

  queryParamMap = of(this.params);
}

describe('GeneBrowserComponent', () => {
  let component: GeneBrowserComponent;
  let fixture: ComponentFixture<GeneBrowserComponent>;

  const activatedRoute = new MockActivatedRoute();
  let testState;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [GeneBrowserComponent],
      providers: [
        DatasetsService,
        UsersService,
        ConfigService,
        FullscreenLoadingService,
        QueryService,
        StateRestoreService,
        {provide: ActivatedRoute, useValue: activatedRoute},
      ],
      imports: [HttpClientTestingModule, RouterTestingModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(GeneBrowserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  beforeEach(() => {
    testState = {
      showDenovo : true,
      showTransmitted : true,
      selectedEffectTypes: ['lgds', 'missense', 'synonymous', 'other'],
      affectedStatus: ['Affected and unaffected'],
      genomicScores: 'testGenomicScores',
      geneSymbols: ['testSymbol'],
      peopleGroup: 'testPeopleGroup',
      datasetId: 'testDatasetId',
      zoomState: {yMin: 0, yMax: 10},
      regions: [1, 10],
      summaryVariantIds: [5, 10, 15],
      selectedVariantTypes: ['sub', 'ins', 'del', 'cnv+', 'cnv-'],
    };
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get current state with assigned dataset id', () => {
    const getCurrentStateSpy = spyOn(QueryStateCollector.prototype, 'getCurrentState').and.returnValue(
      [0] as any
    );
    component.selectedDatasetId = 'testId';
    const state = component.getCurrentState();
    expect(state).toEqual([{datasetId: 'testId'}] as any);
  });

  it('should update shown table preview variants array', () => {
    component.familyLoadingFinished = true;
    const getGenotypePreviewVariantsByFilterSpy = spyOn(component.queryService, 'getGenotypePreviewVariantsByFilter')
      .and.callFake((requestParams, previewInfo) => {
        expect(previewInfo).toEqual(component.genotypePreviewInfo);
        expect(requestParams).toEqual({
          effectTypes: [ 'lgds', 'missense', 'synonymous', 'noStart', 'noEnd', 'no-frame-shift', 'CDS' ],
          genomicScores: [{ metric: 'testMetric', rangeStart: 1, rangeEnd: 11 }],
          inheritanceTypeFilter: [ 'denovo', 'mendelian', 'omission', 'missing' ],
          affectedStatus: [ 'Affected and unaffected', 'Affected only', 'Unaffected only' ],
          geneSymbols: [ 'testSymbol' ],
          datasetId: 'testDatasetId',
          regions: [ 1, 10 ],
          maxVariantsCount: 1,
          summaryVariantIds: [5, 10, 15],
          variant_type: ['sub', 'ins', 'del', 'cnv+', 'cnv-'],
        });
        return 'testPreviewVariantsArray' as any;
      });
    const getCurrentStateSpy = spyOn(component, 'getCurrentState').and.returnValue(of(testState));
    // accesing private property - bad, needs to be refactored
    (component as any).geneBrowserConfig = {frequencyColumn: 'testMetric'};
    component.maxFamilyVariants = 1;

    component.updateShownTablePreviewVariantsArray(new DomainRange(1, 11));
    expect(getGenotypePreviewVariantsByFilterSpy).toHaveBeenCalled();
    expect(getCurrentStateSpy).toHaveBeenCalled();
    expect(component.genotypePreviewVariantsArray).toEqual('testPreviewVariantsArray' as any);
    expect(component.familyLoadingFinished).toBeFalse();
  });

  it('should transform family variants query parameters', () => {
    testState.affectedStatus = ['Affected only'];
    expect(component.transformFamilyVariantsQueryParameters(testState)).toEqual({
      effectTypes: ['lgds', 'missense', 'synonymous', 'noStart', 'noEnd', 'no-frame-shift', 'CDS'],
      genomicScores: 'testGenomicScores',
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
      affectedStatus: ['Affected only'],
      geneSymbols: ['testSymbol'],
      datasetId: 'testDatasetId',
      regions: [1, 10],
      variant_type: ['sub', 'ins', 'del', 'cnv+', 'cnv-']
    });

    testState.affectedStatus = ['Affected and unaffected'];
    expect(component.transformFamilyVariantsQueryParameters(testState).affectedStatus)
      .toEqual(['Affected and unaffected', 'Affected only', 'Unaffected only']);

    testState.showDenovo = false;
    expect(component.transformFamilyVariantsQueryParameters(testState).inheritanceTypeFilter)
      .toEqual(['mendelian', 'omission', 'missing']);

    testState.showDenovo = true;
    testState.showTransmitted = false;
    expect(component.transformFamilyVariantsQueryParameters(testState).inheritanceTypeFilter)
      .toEqual(['denovo']);

    component.enableCodingOnly = false;
    expect(component.transformFamilyVariantsQueryParameters(testState).effectTypes).toEqual([
      'lgds', 'missense', 'synonymous', 'noStart', 'noEnd', 'no-frame-shift',
      'non-coding', 'intron', 'intergenic', '3\'UTR', '3\'UTR-intron', '5\'UTR', '5\'UTR-intron', 'CDS'
    ]);

    testState.selectedEffectTypes = ['missense', 'synonymous'];
    expect(component.transformFamilyVariantsQueryParameters(testState).effectTypes)
      .toEqual(['missense', 'synonymous']);
  });

  it('should submit gene request', () => {
    component.hideResults = true;
    component.enableCodingOnly = true;
    const getCurrentStateSpy = spyOn(component, 'getCurrentState').and.returnValue(of(testState));
    // accesing private property - bad, needs to be refactored
    (component as any).geneService = {
      getGene(gene) { return of('testGene'); },
    };
    spyOn(component.queryService, 'getGenotypePreviewInfo').and.returnValue(of('testGenotypePreviewInfo' as any));
    spyOn(component.queryService, 'getGeneViewVariants').and.callFake((requestParams) => {
      expect(requestParams['showDenovo']).toBeTrue();
      expect(requestParams['showTransmitted']).toBeTrue();
      expect(requestParams['selectedEffectTypes']).toEqual([ 'lgds', 'missense', 'synonymous', 'other' ]);
      expect(requestParams['affectedStatus']).toEqual([ 'Affected and unaffected' ]);
      expect(requestParams['genomicScores']).toEqual('testGenomicScores');
      expect(requestParams['geneSymbols']).toEqual([ 'testSymbol' ]);
      expect(requestParams['peopleGroup']).toEqual('testPeopleGroup');
      expect(requestParams['datasetId']).toEqual('testDatasetId');
      expect(requestParams['summaryVariantIds']).toEqual([ 5, 10, 15 ]);
      expect(requestParams['maxVariantsCount']).toEqual(10000);
      expect(requestParams['inheritanceTypeFilter']).toEqual([ 'denovo', 'mendelian', 'omission', 'missing' ]);
      expect(requestParams['selectedVariantTypes']).toEqual([ 'sub', 'ins', 'del', 'cnv+', 'cnv-' ]);
      if (component.enableCodingOnly) {
        expect(requestParams['effectTypes']).toEqual([ 'lgds', 'nonsense', 'frame-shift', 'splice-site', 'no-frame-shift-newStop',
            'missense', 'synonymous', 'noStart', 'noEnd', 'no-frame-shift', 'CDS' ]);
      } else {
        expect(requestParams['effectTypes']).toEqual(undefined);
      }

      return 'testSummaryVariantsArray' as any;
    });
    component.geneViewComponent = {enableIntronCondensing() {}, disableIntronCondensing() {}} as any;
    const enableIntronCondensingSpy = spyOn(component.geneViewComponent, 'enableIntronCondensing');
    const disableIntronCondensingSpy = spyOn(component.geneViewComponent, 'disableIntronCondensing');

    component.submitGeneRequest();
    expect(component.hideResults).toBeFalse();
    expect(component.geneSymbol).toBe('testSymbol');
    expect(component.selectedGene).toBe('testGene' as any);
    expect(component.genotypePreviewInfo).toBe('testGenotypePreviewInfo' as any);
    expect(component.genotypePreviewVariantsArray).toBe(null);
    expect(enableIntronCondensingSpy).toHaveBeenCalled();
    expect(disableIntronCondensingSpy).not.toHaveBeenCalled();
    expect(component.summaryVariantsArray).toBe('testSummaryVariantsArray' as any);

    component.enableCodingOnly = false;
    component.submitGeneRequest();
    expect(disableIntronCondensingSpy).toHaveBeenCalled();
  });

  it('should get family variant counts', () => {
    component.genotypePreviewVariantsArray = undefined;
    expect(component.getFamilyVariantCounts()).toBe('');

    component.maxFamilyVariants = 12;
    component.genotypePreviewVariantsArray = { getVariantsCount(maxFamilyVariants) {}} as any;
    const getVariantsCountSpy = spyOn(component.genotypePreviewVariantsArray, 'getVariantsCount').and.callFake((variants) => {
      expect(variants).toBe(12);
      return 'variants';
    });
    expect(component.getFamilyVariantCounts()).toBe('variants');
    expect(getVariantsCountSpy).toHaveBeenCalled();
  });

  it('should set on submit event query data to the requested parameters', () => {
    // accesing private property - bad, needs to be refactored
    (component as any).geneBrowserConfig = {frequencyColumn: 'testMetric'};
    const event = {
      target: {queryData: {value: ''}, submit() {}}
    };
    const getCurrentStateSpy = spyOn(component, 'getCurrentState').and.returnValue(of(testState));
    const submitSpy = spyOn(event.target, 'submit').and.callFake(() => {
      expect(event.target.queryData.value).toEqual('{' +
        '"effectTypes":["lgds","missense","synonymous","noStart","noEnd","no-frame-shift","CDS"],' +
        '"genomicScores":[{"metric":"testMetric","rangeStart":null,"rangeEnd":10}],' +
        '"inheritanceTypeFilter":["denovo","mendelian","omission","missing"],' +
        '"affectedStatus":["Affected and unaffected","Affected only","Unaffected only"],' +
        '"variant_type":["sub","ins","del","cnv+","cnv-"],' +
        '"geneSymbols":["testSymbol"],"datasetId":"testDatasetId",' +
        '"regions":[1,10],"summaryVariantIds":[5,10,15]}');
    });

    component.onSubmit(event);
    expect(getCurrentStateSpy).toHaveBeenCalled();
    expect(submitSpy).toHaveBeenCalled();
  });
});
