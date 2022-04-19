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
import { of } from 'rxjs/internal/observable/of';
import { Observable } from 'rxjs/internal/Observable';

class PhenoToolServiceMock {
  public getPhenoToolResults(): Observable<any> {
    return of('fakeValue');
  }
}
class MockDatasetsService {
  getSelectedDataset = function() {
    return { accessRights: true, id: 'testDatasetId' };
  };
}

describe('PhenoToolComponent', () => {
  let component: PhenoToolComponent;
  let fixture: ComponentFixture<PhenoToolComponent>;
  let store: Store;
  const phenoToolMockService = new PhenoToolServiceMock();

  beforeEach(waitForAsync(() => {
    const configMock = { 'baseUrl': 'testUrl/' };
    TestBed.configureTestingModule({
      declarations: [
        PhenoToolComponent,
        // PhenoToolGenotypeBlockComponent,
        GenesBlockComponent,
        GeneSymbolsComponent,
        PhenoToolMeasureComponent,
        // ShareQueryButtonComponent,
        // PhenoMeasureSelectorComponent,
        // ErrorsAlertComponent,
        // SaveQueryComponent,
        // PhenoToolEffectTypesComponent,
        // EffecttypesColumnComponent,
        // CheckboxListComponent,
      ],
      providers: [
        {provide: ActivatedRoute, useValue: new ActivatedRoute()},
        {provide: DatasetsService, useValue: new MockDatasetsService()},
        {provide: ConfigService, useValue: configMock},
        UsersService,
        FullscreenLoadingService,
        {provide: PhenoToolService, useValue: phenoToolMockService},
        MeasuresService,
        // QueryService
      ],
      imports: [
        HttpClientTestingModule,
        RouterTestingModule,
        NgxsModule.forRoot([ErrorsState, GeneSymbolsState]),
        NgbNavModule
      ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
    store = TestBed.inject(Store);
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhenoToolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

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

    expect(mockStateSelector).toEqual(
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
    expect(component.phenoToolResults).toEqual('fakeValue' as any);
  });

  it('should test on download event', () => {
    const form = document.createElement('form');
    form.onsubmit = () => {return false}; // This supresses an error from JSDOM, purely cosmetic
    const event = {target: form};
    event.target.queryData = {
      value: 'id'
    };
    const submitSpy = jest.spyOn(event.target, 'submit');

    component.onDownload(event as any);
    expect(submitSpy).toHaveBeenCalledTimes(1);
    expect(event.target.queryData.value).toEqual('{"datasetId":"testDatasetId"}');
  });

  it('should hide results on a state change', () => {
    fixture.detectChanges();
    component.submitQuery();
    expect(component.phenoToolResults).toEqual('fakeValue' as any);
    store.dispatch(new SetGeneSymbols(['POGZ']));
    expect(component.phenoToolResults).toEqual(null);
  });
});
