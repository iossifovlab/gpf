import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule, Store } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
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

class PhenoToolServiceMock {
  public getPhenoToolResults(): Observable<string> {
    return of('fakeValue');
  }

  public downloadPhenoToolResults(): Observable<HttpResponse<Blob>> {
    return of([] as any);
  }
}
class MockDatasetsService {
  public getSelectedDataset = (): object => ({accessRights: true, id: 'testDatasetId'});
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
        {provide: DatasetsService, useValue: new MockDatasetsService()},
        {provide: ConfigService, useValue: configMock},
        {provide: PhenoToolService, useValue: phenoToolMockService},
        UsersService,
        FullscreenLoadingService,
        MeasuresService,
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NgxsModule.forRoot([ErrorsState, GeneSymbolsState], {developmentMode: true}),
        NgbNavModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
      .compileComponents();
    store = TestBed.inject(Store);
    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
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
    fixture.detectChanges();
    component.submitQuery();
    expect(component.phenoToolResults).toBe('fakeValue' as any);
  });

  it('should hide results on a state change', () => {
    fixture.detectChanges();
    component.submitQuery();
    expect(component.phenoToolResults).toBe('fakeValue' as any);
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

