import { HttpClientTestingModule } from '@angular/common/http/testing';
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
import { HttpResponse } from '@angular/common/http';
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
    // eslint-disable-next-line max-len
    const genotypeBrowserConfigMock = new GenotypeBrowser(true, true, true, true, true, true, true, true, true, new Array<object>(), new Array<PersonFilter>(), new Array<PersonFilter>(), [], [], [], [], 0);
    // eslint-disable-next-line max-len
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
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        StoreModule.forRoot({
          errors: errorsReducer,
          geneSymbols: geneSymbolsReducer,
          datasetId: datasetIdReducer,
          geneSets: geneSetsReducer,
          geneScores: geneScoresReducer,
          phenoToolMeasure: phenoToolMeasureReducer,
          effectTypes: effectTypesReducer,
          presentInParent: presentInParentReducer
        }),
        NgbNavModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;

    store = TestBed.inject(Store);
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should test state selector', () => {
    jest.clearAllMocks();
    const rxjs = jest.requireActual('rxjs');

    const geneSetsMock: GeneSetsState = {
      geneSet: null,
      geneSetsCollection: null,
      geneSetsTypes: null,
    };

    const geneScoresMock: GeneScoresState = {
      score: null,
      rangeStart: 0,
      rangeEnd: 0
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


    jest.spyOn(rxjs, 'combineLatest')
      .mockReturnValue(of([
        [],
        geneSetsMock,
        geneScoresMock,
        phenoToolMeasureMock,
        ['missense', 'splice-site'],
        presentInParentMock
      ]));

    component.ngOnInit();

    expect(component.phenoToolState).toStrictEqual(
      {
        effectTypes: ['missense', 'splice-site'],
        measureId: 'abc',
        normalizeBy: [],
        presentInParent: {
          presentInParent: ['neither'],
          rarity: { ultraRare: false },
        }
      }
    );
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

