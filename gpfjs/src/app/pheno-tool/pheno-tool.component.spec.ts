import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule, Store } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { UsersService } from 'app/users/users.service';
import { PhenoToolComponent } from './pheno-tool.component';
import { PhenoToolService } from './pheno-tool.service';
import { ErrorsState } from 'app/common/errors.state';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { PhenoToolMeasureComponent } from 'app/pheno-tool-measure/pheno-tool-measure.component';
import { MeasuresService } from 'app/measures/measures.service';
import { GeneSymbolsComponent } from 'app/gene-symbols/gene-symbols.component';
import { GeneSymbolsState, SetGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { Observable, of } from 'rxjs';
import { HttpResponse } from '@angular/common/http';
import { PhenoToolResults } from './pheno-tool-results';
import { Dataset, GenotypeBrowser, PersonFilter } from 'app/datasets/datasets';
import { DatasetModel, DatasetState } from 'app/datasets/datasets.state';

class PhenoToolServiceMock {
  public getPhenoToolResults(): Observable<PhenoToolResults> {
    return of(new PhenoToolResults('asdf', []));
  }

  public downloadPhenoToolResults(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }
}

describe('PhenoToolComponent', () => {
  let component: PhenoToolComponent;
  let fixture: ComponentFixture<PhenoToolComponent>;
  let store: Store;
  const phenoToolMockService = new PhenoToolServiceMock();

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
        UsersService,
        FullscreenLoadingService,
        MeasuresService,
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NgxsModule.forRoot([ErrorsState, GeneSymbolsState, DatasetState], {developmentMode: true}),
        NgbNavModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line max-len
    const genotypeBrowserConfigMock = new GenotypeBrowser(true, true, true, true, true, true, true, true, true, new Array<object>(), new Array<PersonFilter>(), new Array<PersonFilter>(), [], [], [], [], 0);
    // eslint-disable-next-line max-len
    const selectedDatasetMock = new Dataset('testId', 'desc', '', 'testDataset', [], true, [], [], [], 'phenotypeData', true, false, true, true, null, genotypeBrowserConfigMock, null, [], null, null, '', null);
    const selectedDatasetMockModel: DatasetModel = {selectedDataset: selectedDatasetMock};

    store = TestBed.inject(Store);
    jest.spyOn(store, 'selectOnce').mockReturnValue(of(selectedDatasetMockModel));

    component.ngOnInit();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should test state selector', () => {
    const mockStateSelector = PhenoToolComponent.phenoToolStateSelector({
      genesBlockState: 'state1',
      testGene: 'test1'
    }, {
      measureState: 'state2',
      testMeasure: 'test2'
    }, {
      genotypeState: 'state3',
      testGeno: 'test3'
    }, {
      familyFilterState: 'state4',
      testFamily: 'test4'
    });

    expect(mockStateSelector).toStrictEqual(
      Object({
        genesBlockState: 'state1',
        testGene: 'test1',
        measureState: 'state2',
        testMeasure: 'test2',
        genotypeState: 'state3',
        testGeno: 'test3',
        familyFilterState: 'state4',
        testFamily: 'test4'
      })
    );
  });

  it('should test submit query', () => {
    component.ngOnInit();
    component.submitQuery();
    expect(component.phenoToolResults).toStrictEqual(new PhenoToolResults('asdf', []));
  });

  it('should hide results on a state change', () => {
    component.ngOnInit();
    component.submitQuery();
    expect(component.phenoToolResults).toStrictEqual(new PhenoToolResults('asdf', []));
    store.dispatch(new SetGeneSymbols(['POGZ']));
    expect(component.phenoToolResults).toBeNull();
  });

  it('should test download', () => {
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

