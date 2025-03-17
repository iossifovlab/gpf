import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { EnrichmentToolComponent } from './enrichment-tool.component';
import { EnrichmentQueryService } from 'app/enrichment-query/enrichment-query.service';
import { Store, StoreModule } from '@ngrx/store';
import { provideHttpClient } from '@angular/common/http';
import { Observable, of, Subscription } from 'rxjs';
import {
  Column,
  Dataset,
  GeneBrowser,
  GenotypeBrowser,
  PersonFilter,
  PersonSet,
  PersonSetCollection,
  PersonSetCollections
} from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from 'app/config/config.service';
import { UserGroup } from 'app/users-groups/users-groups';
import { enrichmentModelsReducer } from 'app/enrichment-models/enrichment-models.state';
import { datasetIdReducer } from 'app/datasets/datasets.state';
import { geneSymbolsReducer } from 'app/gene-symbols/gene-symbols.state';
import { geneSetsReducer } from 'app/gene-sets/gene-sets.state';
import { geneScoresReducer } from 'app/gene-scores/gene-scores.state';
import { errorsReducer } from 'app/common/errors.state';
import { DenovoPersonSetCollection, GeneSet, GeneSetsCollection, GeneSetType } from 'app/gene-sets/gene-sets';
import { EnrichmentResult, EnrichmentResults } from 'app/enrichment-query/enrichment-result';

const datasetMock = new Dataset(
  'datasetId',
  'name1',
  ['parent1', 'parent2'],
  false,
  ['study1', 'study2'],
  ['studyName1', 'studyName2'],
  ['studyType1', 'studyType2'],
  'phenotypeData1',
  false,
  true,
  true,
  false,
  {enabled: true},
  new GenotypeBrowser(
    false,
    true,
    false,
    false,
    true,
    false,
    true,
    false,
    false,
    [
      new Column('name1', 'source1', 'format1'),
      new Column('name2', 'source2', 'format2')
    ],
    [
      new PersonFilter('personFilter1', 'string1', 'source1', 'sourceType1', 'filterType1', 'role1'),
      new PersonFilter('personFilter2', 'string2', 'source2', 'sourceType2', 'filterType2', 'role2')
    ],
    [
      new PersonFilter('familyFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
      new PersonFilter('familyFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
    ],
    ['inheritance', 'string1'],
    ['selectedInheritance', 'string2'],
    ['variant', 'string3'],
    ['selectedVariant', 'string1'],
    5,
    false,
    false
  ),
  new PersonSetCollections(
    [
      new PersonSetCollection(
        'id1',
        'name1',
        [
          new PersonSet('id1', 'name1', 'color1'),
          new PersonSet('id1', 'name2', 'color3'),
          new PersonSet('id2', 'name3', 'color4')
        ]
      ),
      new PersonSetCollection(
        'id2',
        'name2',
        [
          new PersonSet('id2', 'name2', 'color2'),
          new PersonSet('id2', 'name3', 'color5'),
          new PersonSet('id3', 'name4', 'color6')
        ]
      )
    ]
  ),
  [
    new UserGroup(3, 'name1', ['user1', 'user2'], [
      {datasetId: 'dataset2', datasetName: 'dataset2'},
      {datasetId: 'dataset3', datasetName: 'dataset3'}
    ]),
    new UserGroup(5, 'name2', ['user12', 'user5'], [
      {datasetId: 'dataset1', datasetName: 'dataset1'},
      {datasetId: 'dataset2', datasetName: 'dataset2'}
    ])
  ],
  new GeneBrowser(true, 'frequencyCol1', 'frequencyName1', 'effectCol1', 'locationCol1', 5, 6, true),
  false,
  true
);

class DatasetsServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getDataset(id: string): Observable<Dataset> {
    return of(datasetMock);
  }
}

const enrichmentResultsMock = new EnrichmentResults('desc', [new EnrichmentResult('selector', null, null, null, null)]);

class EnrichmentQueryServiceMock {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  public getEnrichmentTest(filter: object): Observable<EnrichmentResults> {
    return of(enrichmentResultsMock);
  }
}
describe('EnrichmentToolComponent', () => {
  let component: EnrichmentToolComponent;
  let fixture: ComponentFixture<EnrichmentToolComponent>;
  let store: Store;
  const datasetsServiceMock = new DatasetsServiceMock();
  const loadingService = new FullscreenLoadingService();
  const enrichmentQueryServiceMock = new EnrichmentQueryServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EnrichmentToolComponent],
      providers: [
        ConfigService,
        { provide: EnrichmentQueryService, useValue: enrichmentQueryServiceMock },
        { provide: FullscreenLoadingService, useValue: loadingService },
        provideHttpClient(),
        { provide: DatasetsService, useValue: datasetsServiceMock }
      ],
      imports: [
        StoreModule.forRoot({
          datasetId: datasetIdReducer,
          geneSymbols: geneSymbolsReducer,
          geneSets: geneSetsReducer,
          geneScores: geneScoresReducer,
          enrichmentModels: enrichmentModelsReducer,
          errors: errorsReducer
        })
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(EnrichmentToolComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set gene symbols when loading from state', () => {
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      datasetMock,
      ['chd8'],
      {
        geneSetsTypes: null,
        geneSetsCollection: null,
        geneSet: null
      },
      {
        histogramType: null,
        score: null,
        rangeStart: null,
        rangeEnd: null,
        values: null,
        categoricalView: null
      },
      [{
        enrichmentBackgroundModel: 'backgroundModel',
        enrichmentCountingModel: 'countingModel'
      }]
    ]));

    component.ngOnInit();

    expect(component.selectedDataset).toStrictEqual(datasetMock);
    expect(component['enrichmentToolState']).toStrictEqual({
      0: {
        enrichmentBackgroundModel: 'backgroundModel',
        enrichmentCountingModel: 'countingModel'
      },
      datasetId: 'datasetId',
      geneSymbols: ['chd8']
    });
  });

  it('should set gene sets when loading from state', () => {
    const geneSet = {
      geneSetsTypes: [
        new GeneSetType('datasetId3', 'datasetName4', [
          new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])
        ])
      ],
      geneSetsCollection:
        new GeneSetsCollection('name1', 'desc2', [
          new GeneSetType(
            'datasetId3',
            'datasetName4',
            [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
          )
        ]),
      geneSet: new GeneSet('name1', 1, 'desc1', 'download1')
    };
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      datasetMock,
      [],
      geneSet,
      {
        histogramType: null,
        score: null,
        rangeStart: null,
        rangeEnd: null,
        values: null,
        categoricalView: null
      },
      [{
        enrichmentBackgroundModel: 'backgroundModel',
        enrichmentCountingModel: 'countingModel'
      }]
    ]));

    component.ngOnInit();

    expect(component.selectedDataset).toStrictEqual(datasetMock);
    expect(component['enrichmentToolState']).toStrictEqual({
      0: {
        enrichmentBackgroundModel: 'backgroundModel',
        enrichmentCountingModel: 'countingModel'
      },
      datasetId: 'datasetId',
      geneSet: {
        geneSet: geneSet.geneSet.name,
        geneSetsCollection: geneSet.geneSetsCollection.name,
        geneSetsTypes: geneSet.geneSetsTypes
      }
    });
  });

  it('should set gene scores when loading from state', () => {
    const geneScores = {
      histogramType: 'categorical',
      score: 'score1',
      rangeStart: null,
      rangeEnd: null,
      values: ['val1', 'val2'],
      categoricalView: 'range selector'
    };
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      datasetMock,
      [],
      {
        geneSetsTypes: null,
        geneSetsCollection: null,
        geneSet: null
      },
      geneScores,
      [{
        enrichmentBackgroundModel: 'backgroundModel',
        enrichmentCountingModel: 'countingModel'
      }]
    ]));

    component.ngOnInit();

    expect(component.selectedDataset).toStrictEqual(datasetMock);
    expect(component['enrichmentToolState']).toStrictEqual({
      0: {
        enrichmentBackgroundModel: 'backgroundModel',
        enrichmentCountingModel: 'countingModel'
      },
      datasetId: 'datasetId',
      geneScores: geneScores
    });
  });

  it('should disable buttons if validation of components fail', () => {
    jest.spyOn(store, 'select').mockReturnValue(of([
      {
        componentId: 'gene sets',
        errors: ['Select gene set']
      }
    ]));
    jest.useFakeTimers();
    const timer: ReturnType<typeof setTimeout> = setTimeout(() => '');
    jest.spyOn(global, 'setTimeout').mockImplementationOnce((fn) => {
      fn();
      return timer;
    });
    component.disableQueryButtons = false;
    component.ngOnInit();
    jest.runAllTimers();

    expect(component.disableQueryButtons).toBe(true);
    jest.useRealTimers();
  });

  it('should interrupt loading', () => {
    const setLoadingStopSpy = jest.spyOn(loadingService, 'setLoadingStop');
    component.enrichmentQuerySubscription = new Subscription();

    component.enrichmentResults = new EnrichmentResults('desc', null);
    expect(component.enrichmentResults).not.toBeNull();
    expect(component.enrichmentQuerySubscription).not.toBeNull();
    loadingService.interruptEvent.emit(true);
    expect(component.enrichmentResults).toBeNull();
    expect(component.enrichmentQuerySubscription).toBeNull();

    expect(setLoadingStopSpy).toHaveBeenCalledWith();
  });

  it('should submit query', () => {
    const setLoadingStartSpy = jest.spyOn(loadingService, 'setLoadingStart');
    const setLoadingStopSpy = jest.spyOn(loadingService, 'setLoadingStop');

    component.submitQuery();
    expect(setLoadingStartSpy).toHaveBeenCalledWith();
    expect(setLoadingStopSpy).toHaveBeenCalledWith();
    expect(component.enrichmentQuerySubscription).not.toBeNull();
    expect(component.enrichmentResults).toStrictEqual(enrichmentResultsMock);
  });
});
