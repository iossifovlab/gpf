import { HttpClient, HttpHandler } from '@angular/common/http';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { QueryService } from 'app/query/query.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { LoadQueryComponent } from './load-query.component';
import { Store, StoreModule } from '@ngrx/store';
import { errorsReducer } from 'app/common/errors.state';
import { Observable, of } from 'rxjs';
import { ActivatedRoute } from '@angular/router';
import { initialState } from 'app/utils/gpf.state';
import { GenotypeBrowserComponent } from 'app/genotype-browser/genotype-browser.component';
import { PhenoBrowserComponent } from 'app/pheno-browser/pheno-browser.component';
import { PhenoToolComponent } from 'app/pheno-tool/pheno-tool.component';
import { EnrichmentToolComponent } from 'app/enrichment-tool/enrichment-tool.component';
import { setGeneScoreCategorical, setGeneScoreContinuous } from 'app/gene-scores/gene-scores.state';

class ActivatedRouteMock {
  public snapshot = {
    params: { uuid: 'abc123' },
    queryParams: { preview: 'false' },
  };
}

initialState.datasetId = 'testDatasetId';
const queryMockGenotypeBrowser = {
  data: initialState,
  page: 'genotype',
};

const queryMockPhenotypeBrowser = {
  data: initialState,
  page: 'phenotype',
};

const queryMockPhenotypeTool = {
  data: initialState,
  page: 'phenotool',
};

const queryMockEnrichmentTool = {
  data: initialState,
  page: 'enrichment',
};

class QueryServiceMock {
  public loadQuery(uuid: string): Observable<object> {
    if (uuid.includes('genotype')) {
      return of(queryMockGenotypeBrowser);
    } else if (uuid.includes('phenotype')) {
      return of(queryMockPhenotypeBrowser);
    } else if (uuid.includes('phenotool')) {
      return of(queryMockPhenotypeTool);
    } else if (uuid.includes('enrichment')) {
      return of(queryMockEnrichmentTool);
    } else {
      return of({});
    }
  }
}

describe('LoadQueryComponent', () => {
  let component: LoadQueryComponent;
  let fixture: ComponentFixture<LoadQueryComponent>;
  const activatedRouteMock = new ActivatedRouteMock();
  const queryServiceMock = new QueryServiceMock();
  let store: Store;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [LoadQueryComponent],
      providers: [
        { provide: QueryService, useValue: queryServiceMock },
        HttpClient,
        HttpHandler,
        ConfigService,
        DatasetsService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: ActivatedRoute, useValue: activatedRouteMock },
      ],
      imports: [
        RouterTestingModule.withRoutes(
          [
            { path: 'datasets/testDatasetId/genotype-browser', component: GenotypeBrowserComponent },
            { path: 'datasets/testDatasetId/phenotype-browser', component: PhenoBrowserComponent },
            { path: 'datasets/testDatasetId/phenotype-tool', component: PhenoToolComponent },
            { path: 'datasets/testDatasetId/enrichment-tool', component: EnrichmentToolComponent },
          ]
        ),
        StoreModule.forRoot({ errors: errorsReducer }),
      ],
    }).compileComponents();
    fixture = TestBed.createComponent(LoadQueryComponent);
    store = TestBed.inject(Store);

    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should navigate to home page when invalid uuid', () => {
    const navigateSpy = jest.spyOn(component['router'], 'navigate');
    activatedRouteMock.snapshot.params = { uuid: null };
    component.ngOnInit();
    expect(navigateSpy).toHaveBeenCalledWith(['/']);
  });

  it('should load query in genotype browser', () => {
    const loadQuerySpy = jest.spyOn(component as any, 'loadQuery'); // spy private method
    const restoreQuerySpy = jest.spyOn(component as any, 'restoreQuery'); // spy private method
    const navigateSpy = jest.spyOn(component['router'], 'navigate');
    activatedRouteMock.snapshot.params = { uuid: 'genotype' };

    component.ngOnInit();

    expect(loadQuerySpy).toHaveBeenCalledWith('genotype', false);
    expect(restoreQuerySpy).toHaveBeenCalledWith(queryMockGenotypeBrowser.data, queryMockGenotypeBrowser.page, false);
    expect(navigateSpy).toHaveBeenCalledWith(['datasets', 'testDatasetId', 'genotype-browser'], {});
  });

  it('should load query in phenotype browser', () => {
    const loadQuerySpy = jest.spyOn(component as any, 'loadQuery'); // spy private method
    const restoreQuerySpy = jest.spyOn(component as any, 'restoreQuery'); // spy private method
    const navigateSpy = jest.spyOn(component['router'], 'navigate');
    activatedRouteMock.snapshot.params = { uuid: 'phenotype' };

    component.ngOnInit();

    expect(loadQuerySpy).toHaveBeenCalledWith('phenotype', false);
    expect(restoreQuerySpy).toHaveBeenCalledWith(queryMockPhenotypeBrowser.data, queryMockPhenotypeBrowser.page, false);
    expect(navigateSpy).toHaveBeenCalledWith(['datasets', 'testDatasetId', 'phenotype-browser'], {});
  });

  it('should load query in phenotype tool', () => {
    const loadQuerySpy = jest.spyOn(component as any, 'loadQuery'); // spy private method
    const restoreQuerySpy = jest.spyOn(component as any, 'restoreQuery'); // spy private method
    const navigateSpy = jest.spyOn(component['router'], 'navigate');
    activatedRouteMock.snapshot.params = { uuid: 'phenotool' };

    component.ngOnInit();

    expect(loadQuerySpy).toHaveBeenCalledWith('phenotool', false);
    expect(restoreQuerySpy).toHaveBeenCalledWith(queryMockPhenotypeTool.data, queryMockPhenotypeTool.page, false);
    expect(navigateSpy).toHaveBeenCalledWith(['datasets', 'testDatasetId', 'phenotype-tool'], {});
  });

  it('should load query in enrichment tool', () => {
    const loadQuerySpy = jest.spyOn(component as any, 'loadQuery'); // spy private method
    const restoreQuerySpy = jest.spyOn(component as any, 'restoreQuery'); // spy private method
    const navigateSpy = jest.spyOn(component['router'], 'navigate');
    activatedRouteMock.snapshot.params = { uuid: 'enrichment' };

    component.ngOnInit();

    expect(loadQuerySpy).toHaveBeenCalledWith('enrichment', false);
    expect(restoreQuerySpy).toHaveBeenCalledWith(queryMockEnrichmentTool.data, queryMockEnrichmentTool.page, false);
    expect(navigateSpy).toHaveBeenCalledWith(['datasets', 'testDatasetId', 'enrichment-tool'], {});
  });

  it('should load query with categorical histogram', () => {
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    initialState.geneScores = {
      histogramType: 'categorical',
      score: 'score1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'range selector',
    };

    component.ngOnInit();

    expect(dispatchSpy).toHaveBeenCalledWith(
      setGeneScoreCategorical({
        score: 'score1',
        values: ['val1', 'val2'],
        categoricalView: 'range selector',
      })
    );
  });

  it('should load query with continuous histogram', () => {
    jest.clearAllMocks();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    initialState.geneScores = {
      histogramType: 'continuous',
      score: 'score1',
      rangeStart: 5,
      rangeEnd: 10,
      values: null,
      categoricalView: null,
    };

    component.ngOnInit();

    expect(dispatchSpy).toHaveBeenCalledWith(
      setGeneScoreContinuous({
        score: 'score1',
        rangeEnd: 10,
        rangeStart: 5,
      })
    );
  });
});
