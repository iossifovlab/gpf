import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { UsersService } from 'app/users/users.service';
import { PhenoToolComponent } from './pheno-tool.component';
import { PhenoToolService } from './pheno-tool.service';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { PhenoToolMeasureComponent } from 'app/pheno-tool-measure/pheno-tool-measure.component';
import { MeasuresService } from 'app/measures/measures.service';
import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Observable, of } from 'rxjs';
import { HttpResponse, provideHttpClient } from '@angular/common/http';
import { PhenoToolResults } from './pheno-tool-results';
import { Dataset, GenotypeBrowser, PersonFilter } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Store, StoreModule } from '@ngrx/store';
import { errorsReducer } from 'app/common/errors.state';
import { geneSymbolsReducer, setGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { geneSetsReducer, GeneSetsState } from 'app/gene-sets/gene-sets.state';
import { geneScoresReducer, GeneScoresState } from 'app/gene-scores/gene-scores.state';
import { phenoToolMeasureReducer, PhenoToolMeasureState } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { PresentInParent, presentInParentReducer } from 'app/present-in-parent/present-in-parent.state';
import { effectTypesReducer } from 'app/effect-types/effect-types.state';
import { personFiltersReducer } from 'app/person-filters/person-filters.state';
import { familyIdsReducer } from 'app/family-ids/family-ids.state';
import { familyTagsReducer } from 'app/family-tags/family-tags.state';
import { genomicScoresReducer, GenomicScoreState } from 'app/genomic-scores-block/genomic-scores-block.state';
import {
  familyMeasureHistogramsReducer,
  MeasureHistogramState,
  personMeasureHistogramsReducer
} from 'app/person-filters-selector/measure-histogram.state';

class PhenoToolServiceMock {
  public getPhenoToolResults(): Observable<PhenoToolResults> {
    return of(new PhenoToolResults('asdf', []));
  }

  public downloadPhenoToolResults(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }
}

class MockDatasetsService {
  public getDataset(datasetId: string): Observable<Dataset> {
    // eslint-disable-next-line @stylistic/max-len
    const genotypeBrowserConfigMock = new GenotypeBrowser(true, true, true, true, true, true, true, true, true, new Array<object>(), new Array<PersonFilter>(), new Array<PersonFilter>(), [], [], [], [], 0, false, false);
    // eslint-disable-next-line @stylistic/max-len
    return of(new Dataset(datasetId, 'testDataset', [], true, [], [], [], '', true, true, true, true, null, genotypeBrowserConfigMock, null, [], null, null, '', null));
  }
}

describe('PhenoToolComponent', () => {
  let component: PhenoToolComponent;
  let fixture: ComponentFixture<PhenoToolComponent>;
  let store: Store;
  const phenoToolMockService = new PhenoToolServiceMock();
  const mockDatasetsService = new MockDatasetsService();

  beforeEach(waitForAsync(() => {
    const configMock = { baseUrl: 'testUrl/' };
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolComponent,
        GenesBlockComponent,
        GeneSymbolsComponent,
        PhenoToolMeasureComponent,
      ],
      providers: [
        {provide: ActivatedRoute, useValue: new ActivatedRoute()},
        {provide: ConfigService, useValue: configMock},
        {provide: PhenoToolService, useValue: phenoToolMockService},
        { provide: DatasetsService, useValue: mockDatasetsService },
        UsersService,
        FullscreenLoadingService,
        MeasuresService,
        provideHttpClient(),
        provideHttpClientTesting()
      ],
      imports: [
        RouterTestingModule,
        StoreModule.forRoot({
          errors: errorsReducer,
          geneSymbols: geneSymbolsReducer,
          datasetId: datasetIdReducer,
          geneSets: geneSetsReducer,
          geneScores: geneScoresReducer,
          phenoToolMeasure: phenoToolMeasureReducer,
          effectTypes: effectTypesReducer,
          presentInParent: presentInParentReducer,
          personFilters: personFiltersReducer,
          familyIds: familyIdsReducer,
          familyTags: familyTagsReducer,
          genomicScores: genomicScoresReducer,
          familyMeasureHistograms: familyMeasureHistogramsReducer,
          personMeasureHistograms: personMeasureHistogramsReducer
        }),
        NgbNavModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get and combine states of all filters', () => {
    jest.clearAllMocks();
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');

    const geneSetsMock: GeneSetsState = {
      geneSet: null,
      geneSetsCollection: null,
      geneSetsTypes: null,
    };

    const geneScoresMock: GeneScoresState = {
      histogramType: null,
      score: null,
      rangeStart: 0,
      rangeEnd: 0,
      values: null,
      categoricalView: null,
    };

    const phenoToolMeasureMock: PhenoToolMeasureState = {
      measureId: 'abc',
      normalizeBy: []
    };

    const presentInParentMock: PresentInParent = {
      presentInParent: ['neither'],
      rarity: {
        rarityType: '',
        rarityIntervalStart: 0,
        rarityIntervalEnd: 1,
      }
    };

    const genomicScoresMock: GenomicScoreState = {
      histogramType: 'categorical',
      score: 's1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'click selector'
    };

    const familyMeasureHistogramsMock: MeasureHistogramState = {
      histogramType: 'categorical',
      measure: 'm1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'click selector',
      roles: null
    };

    const personMeasureHistogramsMock: MeasureHistogramState = {
      histogramType: 'continuous',
      measure: 'm2',
      rangeStart: 5,
      rangeEnd: 100,
      values: null,
      categoricalView: null,
      roles: null
    };

    jest.spyOn(rxjs, 'combineLatest')
      .mockReturnValue(of([
        [],
        geneSetsMock,
        geneScoresMock,
        phenoToolMeasureMock,
        ['missense', 'splice-site'],
        presentInParentMock,
        {
          selectedFamilyTags: [],
          deselectedFamilyTags: [],
          tagIntersection: true,
        },
        [],
        {
          familyFilters: null,
          personFilters: null,
        },
        [familyMeasureHistogramsMock],
        [personMeasureHistogramsMock],
        genomicScoresMock
      ]));

    component.ngOnInit();

    const phenoToolStateResult = {
      effectTypes: ['missense', 'splice-site'],
      familyFiltersBeta: [{
        source: 'm1',
        isFamily: true,
        histogramType: 'categorical',
        min: null,
        max: null,
        values: ['val1', 'val2'],
        roles: null
      }],
      genomicScores: genomicScoresMock,
      measureId: 'abc',
      normalizeBy: [],
      personFiltersBeta: [{
        source: 'm2',
        isFamily: false,
        histogramType: 'continuous',
        min: 5,
        max: 100,
        values: null,
        roles: null
      }],
      presentInParent: {
        presentInParent: ['neither'],
        rarity: { ultraRare: false },
      },
    };

    expect(component.phenoToolState).toStrictEqual(phenoToolStateResult);
  });

  it('should test submit query', () => {
    component.ngOnInit();
    component.submitQuery();
    expect(component.phenoToolResults).toStrictEqual(new PhenoToolResults('asdf', []));
  });

  it('should hide results on a state change', () => {
    jest.clearAllMocks();
    jest.restoreAllMocks();

    component.ngOnInit();
    expect(component.phenoToolResults).toBeNull();
    component.submitQuery();
    expect(component.phenoToolResults).toStrictEqual(new PhenoToolResults('asdf', []));
    store.dispatch(setGeneSymbols({geneSymbols: ['POGZ']}));
    expect(component.phenoToolResults).toBeNull();
  });

  it('should test download', () => {
    component.ngOnInit();
    const mockEvent = {
      target: document.createElement('form'),
      preventDefault: jest.fn()
    };
    mockEvent.target.queryData = {
      value: ''
    };
    jest.spyOn(mockEvent.target, 'submit').mockImplementation();
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-explicit-any
    component.onDownload(mockEvent as any);

    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    expect(mockEvent.target.queryData.value).toStrictEqual(JSON.stringify({
      ...component.phenoToolState,
      datasetId: component.selectedDataset.id
    }));
    expect(mockEvent.target.submit).toHaveBeenCalledTimes(1);
  });
});

