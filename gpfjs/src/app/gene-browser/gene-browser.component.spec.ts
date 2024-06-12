import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, NavigationStart, Router, RouterEvent } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { Observable, of, Subject } from 'rxjs';
import { GeneSymbolsState } from 'app/gene-symbols/gene-symbols.state';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { QueryService } from 'app/query/query.service';
import { UsersService } from 'app/users/users.service';
import { GeneService } from './gene.service';
import { GeneBrowserComponent } from './gene-browser.component';
import { FormsModule } from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { SummaryAllelesArray, SummaryAllelesFilter } from './summary-variants';
import { GenePlotComponent } from 'app/gene-plot/gene-plot.component';
import { GenotypePreviewTableComponent } from 'app/genotype-preview-table/genotype-preview-table.component';
import { APP_BASE_HREF } from '@angular/common';
import { HttpResponse } from '@angular/common/http';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import {
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY,
  MatAutocomplete,
  MatAutocompleteOrigin,
  MatAutocompleteTrigger } from '@angular/material/autocomplete';

jest.mock('../utils/svg-drawing');

class MockActivatedRoute {
  public static params = {dataset: 'testDatasetId', get: (): string => ''};
  // eslint-disable-next-line @typescript-eslint/naming-convention
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

class MockQueryService {
  public downloadVariantsSummary(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }

  public getSummaryVariants(): Observable<object> {
    return of([]);
  }

  public downloadVariants(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }

  public streamingFinishedSubject = new Subject();
  public summaryStreamingFinishedSubject = new Subject();

  public ngOnInit(): void {
    this.streamingFinishedSubject.next([]);
    this.summaryStreamingFinishedSubject.next([]);
  }

  public cancelStreamPost(): void {
    return null;
  }
}

describe('GeneBrowserComponent', () => {
  let component: GeneBrowserComponent;
  let fixture: ComponentFixture<GeneBrowserComponent>;
  const mockDatasetsService = new MockDatasetsService();
  const mockQueryService = new MockQueryService();
  let loadingService: FullscreenLoadingService;

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [
        GeneBrowserComponent, GenePlotComponent,
        GenotypePreviewTableComponent,
        MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger
      ],
      providers: [
        ConfigService, UsersService, DatasetsTreeService, FullscreenLoadingService,
        {provide: QueryService, useValue: mockQueryService},
        {provide: ActivatedRoute, useValue: new MockActivatedRoute()},
        {provide: GeneService, useValue: new MockGeneService()},
        {provide: DatasetsService, useValue: mockDatasetsService},
        {provide: APP_BASE_HREF, useValue: ''},
        {provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''}
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule,
        NgxsModule.forRoot([GeneSymbolsState], {developmentMode: true}),
        NgbModule, FormsModule
      ],
    }).compileComponents();

    jest.clearAllMocks();
    fixture = TestBed.createComponent(GeneBrowserComponent);
    component = fixture.componentInstance;
    loadingService = TestBed.inject(FullscreenLoadingService);
    component.summaryVariantsArray = new SummaryAllelesArray();
    jest.spyOn(component['queryService'], 'getSummaryVariants');
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
    expect(component['drawDenovoIcons']).toHaveBeenCalledWith();
    expect(component['drawTransmittedIcons']).toHaveBeenCalledWith();
    expect(component['drawEffectTypesIcons']).toHaveBeenCalledWith();
  });

  it('should select affected status', () => {
    // There are default values to account for, so we use prevLength
    const prevLength = component.summaryVariantsFilter.selectedAffectedStatus.size;
    component.checkAffectedStatus('test', true);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toStrictEqual(prevLength + 1);
    component.checkAffectedStatus('test', false);
    expect(component.summaryVariantsFilter.selectedAffectedStatus.size).toStrictEqual(prevLength);
  });

  it('should select effect type', () => {
    const prevLength = component.summaryVariantsFilter.selectedEffectTypes.size;
    component.checkEffectType('test', true);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toStrictEqual(prevLength + 1);
    component.checkEffectType('test', false);
    expect(component.summaryVariantsFilter.selectedEffectTypes.size).toStrictEqual(prevLength);
  });

  it('should select variant type', () => {
    const prevLength = component.summaryVariantsFilter.selectedVariantTypes.size;
    component.checkVariantType('test', true);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toStrictEqual(prevLength + 1);
    component.checkVariantType('test', false);
    expect(component.summaryVariantsFilter.selectedVariantTypes.size).toStrictEqual(prevLength);
  });

  it('should toggle denovo', () => {
    component.checkShowDenovo(true);
    expect(component.summaryVariantsFilter.denovo).toBe(true);
    component.checkShowDenovo(false);
    expect(component.summaryVariantsFilter.denovo).toBe(false);
  });

  it('should toggle transmitted', () => {
    component.checkShowTransmitted(true);
    expect(component.summaryVariantsFilter.transmitted).toBe(true);
    component.checkShowTransmitted(false);
    expect(component.summaryVariantsFilter.transmitted).toBe(false);
  });

  it('should set selected region', () => {
    jest.spyOn(component, 'updateVariants');
    component.setSelectedRegion([1, 2]);
    expect(component.summaryVariantsFilter.selectedRegion).toStrictEqual([1, 2]);
    expect(component['updateVariants']).toHaveBeenCalledWith();
  });

  it('should set selected frequencies', () => {
    jest.spyOn(component, 'updateVariants');
    component.setSelectedFrequencies([3, 4]);
    expect(component.summaryVariantsFilter.selectedFrequencies).toStrictEqual([3, 4]);
    expect(component['updateVariants']).toHaveBeenCalledWith();
  });

  it('should not reset coding only on request and properly handle CNV and Other effect types', () => {
    component.summaryVariantsFilter = new SummaryAllelesFilter(true, true, false);
    component.effectTypeValues.forEach(eff => component.checkEffectType(eff, true));

    // Make sure "Coding only" didn't get re-toggled
    expect(component.summaryVariantsFilter.queryParams['effectTypes']).toStrictEqual([
      'frame-shift', 'nonsense', 'splice-site', 'no-frame-shift-newStop',
      'missense', 'synonymous', 'CNV+', 'CNV-', '3\'UTR', '3\'UTR-intron', '5\'UTR', '5\'UTR-intron',
      'intergenic', 'intron', 'no-frame-shift', 'noEnd', 'noStart', 'non-coding', 'non-coding-intron', 'CDS',
    ]);

    // Untoggling "Other" shouldn't remove CNVs
    component.checkEffectType('Other', false);
    expect(component.summaryVariantsFilter.queryParams['effectTypes']).toStrictEqual([
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
    expect(component.summaryVariantsFilter.queryParams).toStrictEqual({
      effectTypes: ['CNV+', 'missense'],
      inheritanceTypeFilter: ['denovo'],
      affectedStatus: ['Affected only'],
      variantTypes: ['sub']
    });
    await component.submitGeneRequest('POGZ');
    expect(component.summaryVariantsFilter.queryParams).toStrictEqual({
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
      variantTypes: ['sub', 'ins', 'del', 'CNV+', 'CNV-', 'comp']
    });
  });

  it('should get family variants count when count is less than 1000', () => {
    component.familyVariantsLoaded = false;

    const summaryVariantsArrayFilteredMock = new SummaryAllelesArray([], []);
    component.summaryVariantsArrayFiltered = summaryVariantsArrayFilteredMock;
    jest.spyOn(component.summaryVariantsArrayFiltered, 'totalFamilyVariantsCount', 'get').mockReturnValue(5);

    expect(component.displayVariantsCount()).toBe('~5');
  });

  it('should get family variants count when count is more than 1000', () => {
    component.familyVariantsLoaded = false;

    const summaryVariantsArrayFilteredMock = new SummaryAllelesArray([], []);
    component.summaryVariantsArrayFiltered = summaryVariantsArrayFilteredMock;
    jest.spyOn(component.summaryVariantsArrayFiltered, 'totalFamilyVariantsCount', 'get').mockReturnValue(9635);
    expect(component.displayVariantsCount()).toBe('9635');
  });

  it('should get family variants count when count is 0', () => {
    component.familyVariantsLoaded = false;

    const summaryVariantsArrayFilteredMock = new SummaryAllelesArray([], []);
    component.summaryVariantsArrayFiltered = summaryVariantsArrayFilteredMock;
    jest.spyOn(component.summaryVariantsArrayFiltered, 'totalFamilyVariantsCount', 'get').mockReturnValue(0);
    expect(component.displayVariantsCount()).toBe('0');
  });

  it('should get family variants count after loading variants is finished', () => {
    component.familyVariantsLoaded = false;

    const summaryVariantsArrayFilteredMock = new SummaryAllelesArray([], []);
    component.summaryVariantsArrayFiltered = summaryVariantsArrayFilteredMock;
    jest.spyOn(component.summaryVariantsArrayFiltered, 'totalFamilyVariantsCount', 'get').mockReturnValue(35);
    expect(component.displayVariantsCount()).toBe('~35');

    component.familyVariantsLoaded = true;
    component.variantsCount = 20;
    expect(component.displayVariantsCount()).toBe('20');
  });

  it('should get family variants count when loaded count is 0', () => {
    component.familyVariantsLoaded = false;

    const summaryVariantsArrayFilteredMock = new SummaryAllelesArray([], []);
    component.summaryVariantsArrayFiltered = summaryVariantsArrayFilteredMock;
    jest.spyOn(component.summaryVariantsArrayFiltered, 'totalFamilyVariantsCount', 'get').mockReturnValue(7412);
    expect(component.displayVariantsCount()).toBe('7412');

    component.familyVariantsLoaded = true;
    component.variantsCount = 0;
    expect(component.displayVariantsCount()).toBe('0');
  });

  it('should get family variants count when loaded count is more than 1000', () => {
    component.familyVariantsLoaded = false;

    const summaryVariantsArrayFilteredMock = new SummaryAllelesArray([], []);
    component.summaryVariantsArrayFiltered = summaryVariantsArrayFilteredMock;
    jest.spyOn(component.summaryVariantsArrayFiltered, 'totalFamilyVariantsCount', 'get').mockReturnValue(7412);
    expect(component.displayVariantsCount()).toBe('7412');

    component.familyVariantsLoaded = true;
    component.variantsCount = -1;
    expect(component.displayVariantsCount()).toBe('7412');
  });

  it.skip('should test download', () => {
    const mockEvent = {
      target: {
        queryData: {
          value: ''
        },
        submit: jest.fn()
      }
    };

    component.onSubmit(mockEvent as unknown as Event);

    expect(mockEvent.target.queryData.value).toStrictEqual(JSON.stringify({
      effectTypes: [
        'frame-shift',
        'nonsense',
        'splice-site',
        'no-frame-shift-newStop',
        'missense',
        'synonymous',
        'CNV+',
        'CNV-',
        '3\'UTR',
        '3\'UTR-intron',
        '5\'UTR',
        '5\'UTR-intron',
        'intergenic',
        'intron',
        'no-frame-shift',
        'noEnd',
        'noStart',
        'non-coding',
        'non-coding-intron',
        'CDS'
      ],
      inheritanceTypeFilter: ['denovo', 'mendelian', 'omission', 'missing'],
      affectedStatus: ['Affected only', 'Unaffected only', 'Affected and unaffected'],
      variantTypes: ['sub', 'ins', 'del', 'CNV+', 'CNV-', 'comp'],
      geneSymbols: ['POGZ'],
      datasetId: 'testDatasetId',
      regions: '',
      summaryVariantIds: [],
      genomicScores: [{ metric: 'testColumn', rangeStart: null, rangeEnd: 100 }],
      download: true
    }));
    expect(mockEvent.target.submit).toHaveBeenCalledTimes(1);
  });

  it.skip('should cancel queries on router change', () => {
    const stopSpy = jest.spyOn(loadingService, 'setLoadingStop');
    const cancelSpy = jest.spyOn(mockQueryService, 'cancelStreamPost');
    const router = TestBed.inject(Router);

    (router.events as Subject<RouterEvent>).next(new NavigationStart(1, 'start'));

    expect(stopSpy).toHaveBeenCalledTimes(1);
    expect(cancelSpy).toHaveBeenCalledTimes(1);
  });

  it.skip('should cancel request on loading service interrupt', () => {
    const spyOnSummaryVariants = jest.spyOn(mockQueryService, 'getSummaryVariants');
    const spyOnCancelSummaryPost = jest.spyOn(mockQueryService, 'cancelStreamPost');
    component.submitGeneRequest('CHD8');
    expect(spyOnSummaryVariants).toHaveBeenCalledTimes(1);
    loadingService.interruptEvent.emit(true);
    expect(spyOnSummaryVariants).toHaveBeenCalledTimes(1);
    expect(spyOnCancelSummaryPost).toHaveBeenCalledTimes(1);
  });
});
