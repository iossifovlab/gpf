import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { Observable, of } from 'rxjs';
import { GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { QueryService } from 'app/query/query.service';
import { UsersService } from 'app/users/users.service';
import { GeneService } from './gene.service';
import { GeneBrowserComponent } from './gene-browser.component';
import { SearchableSelectComponent } from '../searchable-select/searchable-select.component';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { SummaryAllelesArray, SummaryAllelesFilter } from './summary-variants';
import { GenePlotComponent } from 'app/gene-plot/gene-plot.component';
import { GenotypePreviewTableComponent } from 'app/genotype-preview-table/genotype-preview-table.component';
import { APP_BASE_HREF } from '@angular/common';

jest.mock('../utils/svg-drawing');

class MockActivatedRoute {
  public static params = {dataset: 'testDatasetId', get: (): string => ''};
  public queryParams = of({coding_only: true});
  public parent = {params: of(MockActivatedRoute.params)};
  public queryParamMap = of(MockActivatedRoute.params);
  public snapshot = {params: {gene: 'mockGeneSymbol'}};
}

class MockDatasetsService {
  public getSelectedDataset(): Record<string, unknown> {
    return {
      id: 'testDataset',
      geneBrowser: { domainMax: 100, frequencyColumn: 'testColumn'},
      personSetCollections: { getLegend: (): Array<unknown> => [] },
    };
  }
}

class MockGeneService {
  public getGene(): Observable<Record<string, unknown>> {
    return of({
      geneSymbol: 'POGZ',
      collapsedTranscripts: [{
        start: 1,
        stop: 2
      }],
      getRegionString: () => ''
    });
  }
}

describe('GeneBrowserComponent', () => {
  let component: GeneBrowserComponent;
  let fixture: ComponentFixture<GeneBrowserComponent>;
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [
        GeneBrowserComponent, GenePlotComponent,
        GenotypePreviewTableComponent, SearchableSelectComponent
      ],
      providers: [
        ConfigService, UsersService, FullscreenLoadingService, QueryService,
        {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
        {provide: GeneService, useValue: new MockGeneService()},
        {provide: DatasetsService, useValue: mockDatasetsService},
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule,
        NgxsModule.forRoot([GeneSymbolsState], {developmentMode: true}),
        NgbModule, FormsModule
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(GeneBrowserComponent);
    component = fixture.componentInstance;
    component.summaryVariantsArray = new SummaryAllelesArray();
    jest.spyOn<any, any>(component['queryService'], 'getSummaryVariants').mockImplementation(
      () => new SummaryAllelesArray()
    );
    fixture.detectChanges();
  });


  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should draw legend on filters div set', () => {
    expect(component).toBeTruthy();
    jest.spyOn<any, any>(component, 'drawDenovoIcons').mockImplementation(() => null);
    jest.spyOn<any, any>(component, 'drawTransmittedIcons').mockImplementation(() => null);
    jest.spyOn<any, any>(component, 'drawEffectTypesIcons').mockImplementation(() => null);
    component.filters = null;
    expect(component['drawDenovoIcons']).toHaveBeenCalled();
    expect(component['drawTransmittedIcons']).toHaveBeenCalled();
    expect(component['drawEffectTypesIcons']).toHaveBeenCalled();
  });

  it('should select affected status', () => {
    // There are default values to account for, so we use prevLength
    const prevLength = component.summaryVariantsFilter.selectedAffectedStatus.size;
    component.checkAffectedStatus('test', true);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toEqual(prevLength + 1);
    component.checkAffectedStatus('test', false);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toEqual(prevLength);
  });

  it('should select effect type', () => {
    const prevLength = component.summaryVariantsFilter.selectedEffectTypes.size;
    component.checkEffectType('test', true);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toEqual(prevLength + 1);
    component.checkEffectType('test', false);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toEqual(prevLength);
  });

  it('should select variant type', () => {
    const prevLength = component.summaryVariantsFilter.selectedVariantTypes.size;
    component.checkVariantType('test', true);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toEqual(prevLength + 1);
    component.checkVariantType('test', false);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toEqual(prevLength);
  });

  it('should toggle denovo', () => {
    component.checkShowDenovo(true);
    expect(component.summaryVariantsFilter.denovo).toEqual(true);
    component.checkShowDenovo(false);
    expect(component.summaryVariantsFilter.denovo).toEqual(false);
  });

  it('should toggle transmitted', () => {
    component.checkShowTransmitted(true);
    expect(component.summaryVariantsFilter.transmitted).toEqual(true);
    component.checkShowTransmitted(false);
    expect(component.summaryVariantsFilter.transmitted).toEqual(false);
  });

  it('should set selected region', () => {
    jest.spyOn<any, any>(component, 'updateVariants');
    component.setSelectedRegion([1, 2]);
    expect(component.summaryVariantsFilter.selectedRegion).toEqual([1, 2]);
    expect(component['updateVariants']).toHaveBeenCalled();
  });

  it('should set selected frequencies', () => {
    jest.spyOn<any, any>(component, 'updateVariants');
    component.setSelectedFrequencies([3, 4]);
    expect(component.summaryVariantsFilter.selectedFrequencies).toEqual([3, 4]);
    expect(component['updateVariants']).toHaveBeenCalled();
  });

  it('should not reset coding only on request and properly handle CNV and Other effect types', () => {
    component.summaryVariantsFilter = new SummaryAllelesFilter(true, true, false);
    component.effectTypeValues.forEach(eff => component.checkEffectType(eff, true));

    // Make sure "Coding only" didn't get re-toggled
    expect(component.summaryVariantsFilter.queryParams['effectTypes']).toEqual([
      'frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop',
      'missense', 'synonymous', 'CNV+', 'CNV-', '3\'UTR', '3\'UTR-intron', '5\'UTR', '5\'UTR-intron',
      'intergenic', 'intron', 'no-frame-shift', 'noEnd', 'noStart', 'non-coding', 'non-coding-intron', 'CDS',
    ]);

    // Untoggling "Other" shouldn't remove CNVs
    component.checkEffectType('Other', false);
    expect(component.summaryVariantsFilter.queryParams['effectTypes']).toEqual([
      'frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop',
      'missense', 'synonymous', 'CNV+', 'CNV-'
    ]);
  });

  it('should reset filters on new request', async() => {
    jest.spyOn<any, any>(component, 'updateShownTablePreviewVariantsArray').mockImplementation(() => null);
    component.summaryVariantsFilter = new SummaryAllelesFilter(true, false, true);
    component.checkEffectType('CNV+', true);
    component.checkEffectType('missense', true);
    component.checkVariantType('sub', true);
    component.checkAffectedStatus('Affected only', true);
    expect(component.summaryVariantsFilter.queryParams).toEqual({
      effectTypes: ['CNV+', 'missense'],
      inheritanceTypeFilter: ['denovo'],
      affectedStatus: ['Affected only'],
      variantTypes: ['sub']
    });
    await component.submitGeneRequest('POGZ');
    expect(component.summaryVariantsFilter.queryParams).toEqual({
      effectTypes: [
        'frame-shift',
        'nonsense',
        'splice-site',
        'no-frame-shift-newStop',
        'missense',
        'synonymous',
        'CNV+',
        'CNV-',
        'no-frame-shift',
        'noEnd',
        'noStart',
        'CDS'
      ],
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
      affectedStatus: ['Affected only', 'Unaffected only', 'Affected and unaffected'],
      variantTypes: ['sub', 'ins', 'del', 'CNV+', 'CNV-']
    });
  });

  it('should test download', () => {
    const spy = jest.spyOn(component, 'onDownloadSummary');
    component.onDownloadSummary();
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
