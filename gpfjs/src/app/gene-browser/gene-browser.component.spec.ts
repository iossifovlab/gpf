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
import { treemapResquarify } from 'd3';
import { Observable } from 'rxjs/internal/Observable';
import { of } from 'rxjs/internal/observable/of';
import { MapOperator } from 'rxjs/internal/operators/map';
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
      regions: [1, 10]
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

  // it('should update shown table preview variants array', () => {
  //   const getGenotypePreviewVariantsByFilterSpy = spyOn(component.queryService, 'getGenotypePreviewVariantsByFilter')
  //     .and.callFake((requestParams, previewInfo) => {
  //       expect(previewInfo).toEqual(component.genotypePreviewInfo);
  //       console.log(requestParams);
  //       return 'testPreviewVariantsArray' as any;
  //     });
  //   const getCurrentStateSpy = spyOn(component, 'getCurrentState').and.returnValue(testState);
  //   component.maxFamilyVariants = 1;
  //   component.updateShownTablePreviewVariantsArray(new DomainRange(1, 11));
  //   console.log(component.genotypePreviewVariantsArray);
  //   // expect(component.genotypePreviewVariantsArray).toEqual([] as any);
  // });
  it('should transform family variants query parameters', () => {
    testState.affectedStatus = ['Affected only'];
    expect(component.transformFamilyVariantsQueryParameters(testState)).toEqual({
      effectTypes: ['lgds', 'missense', 'synonymous', 'noStart', 'noEnd', 'no-frame-shift', 'CDS'],
      genomicScores: 'testGenomicScores',
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
      affectedStatus: ['Affected only'],
      geneSymbols: ['testSymbol'],
      datasetId: 'testDatasetId',
      regions: [1, 10]
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
});
