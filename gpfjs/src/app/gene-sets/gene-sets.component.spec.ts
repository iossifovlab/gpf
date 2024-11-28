import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { UsersService } from 'app/users/users.service';
import { GeneSetsComponent } from './gene-sets.component';
import { GeneSetsService } from './gene-sets.service';
import { NgbAccordionModule, NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { BrowserModule } from '@angular/platform-browser';
import { CommonModule, APP_BASE_HREF } from '@angular/common';
import {
  DenovoPersonSetCollection,
  GeneSet,
  GeneSetsCollection,
  GeneSetType,
  GeneSetTypeNode,
  SelectedDenovoTypes,
  SelectedPersonSetCollections } from './gene-sets';
import { Observable } from 'rxjs/internal/Observable';
import { of } from 'rxjs';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { geneSetsReducer } from './gene-sets.state';
import {
  MatAutocompleteOrigin,
  MatAutocomplete,
  MatAutocompleteTrigger,
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY } from '@angular/material/autocomplete';
import { StoreModule, Store } from '@ngrx/store';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { DatasetHierarchy, PersonSet } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';

const denovoGeneSetsMock = [
  new GeneSetType(
    'SSC_genotypes',
    'SSC Genotypes',
    [new DenovoPersonSetCollection('phenotype', 'phenotype', [
      new PersonSet('autism', 'autism', '#0000'),
      new PersonSet('unaffected', 'unaffected', '#0000'),
    ])]
  ),
  new GeneSetType(
    'SFARI_SSC_WGS_2',
    'SSC NYGC WGS',
    [new DenovoPersonSetCollection('phenotype', 'phenotype', [
      new PersonSet('autism', 'autism', '#0000'),
      new PersonSet('unaffected', 'unaffected', '#0000'),
    ])]
  ),

  new GeneSetType(
    'ssc_rna_seq',
    'SSC LCL RNA Sequencing',
    [new DenovoPersonSetCollection('phenotype', 'phenotype', [
      new PersonSet('autism', 'autism', '#0000'),
      new PersonSet('unaffected', 'unaffected', '#0000'),
    ])]
  ),
  new GeneSetType(
    'SFARI_SSC_WGS_CSHL',
    'SSC CSHL WGS',
    [new DenovoPersonSetCollection('phenotype', 'phenotype', [
      new PersonSet('autism', 'autism', '#0000'),
      new PersonSet('unaffected', 'unaffected', '#0000'),
    ])]
  )
];

const geneSetsCollectionMock = [
  new GeneSetsCollection('denovo', 'desc2',
    [
      new GeneSetType(
        'id3',
        'datasetName4',
        [new DenovoPersonSetCollection('phenotype', 'phenotype', [
          new PersonSet('autism', 'autism', '#0000'),
          new PersonSet('unaffected', 'unaffected', '#0000'),
        ])]
      ),
      new GeneSetType(
        'id9',
        'datasetName10',
        [new DenovoPersonSetCollection('phenotype', 'phenotype', [
          new PersonSet('autism', 'autism', '#0000'),
          new PersonSet('unaffected', 'unaffected', '#0000'),
        ])]
      )
    ]
  ),
  new GeneSetsCollection('name15', 'desc16',
    [
      new GeneSetType(
        'id17',
        'datasetName18',
        [new DenovoPersonSetCollection('phenotype', 'phenotype', [
          new PersonSet('autism', 'autism', '#0000'),
          new PersonSet('unaffected', 'unaffected', '#0000'),
        ])]
      ),
      new GeneSetType(
        'id23',
        'datasetName24',
        [new DenovoPersonSetCollection('phenotype', 'phenotype', [
          new PersonSet('autism', 'autism', '#0000'),
          new PersonSet('unaffected', 'unaffected', '#0000'),
        ])]
      )
    ]
  )
];
class MockGeneSetsService {
  public provide = true;

  public getGeneSets(): Observable<GeneSet[]> {
    if (this.provide) {
      return of([new GeneSet('name1', 2, 'desc3', 'download4'), new GeneSet('name5', 6, 'desc7', 'download8')]);
    } else {
      return of(undefined);
    }
  }

  public getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    if (this.provide) {
      return of(geneSetsCollectionMock);
    } else {
      return of(undefined);
    }
  }

  public getDenovoGeneSets(): Observable<GeneSetType[]> {
    if (this.provide) {
      return of(denovoGeneSetsMock);
    } else {
      return of(undefined);
    }
  }
}

const datasetHierarchyMock = [
  new DatasetHierarchy(
    'SSC_genotypes',
    'SSC Genotypes',
    true,
    [
      new DatasetHierarchy('SFARI_SSC_WGS_2', 'SSC NYGC WGS', true, null),
      new DatasetHierarchy('SFARI_SSC_WGS_CSHL', 'SSC CSHL WGS', true, [
        new DatasetHierarchy('SFARI_SSC_WGS_CSHLChild1', 'SSC CSHL WGS', true, null),
        new DatasetHierarchy('SFARI_SSC_WGS_CSHLChild2', 'SSC CSHL WGS', true, null)
      ]),
    ]
  ),
  new DatasetHierarchy(
    'ssc_rna_seq',
    'SSC LCL RNA Sequencing',
    true,
    []
  )
];

class MockDatasetsTreeService {
  public getDatasetHierarchy(): Observable<DatasetHierarchy[]> {
    return of(datasetHierarchyMock);
  }
}

const visibleDatasetsMock = ['SSC_genotypes', 'ssc_rna_seq', 'SFARI_SSC_WGS_2', 'SFARI_SSC_WGS_CSHL'];

class DatasetsServiceMock {
  public getVisibleDatasets(): Observable<string[]> {
    return of(visibleDatasetsMock);
  }
}

describe('GeneSetsComponent', () => {
  let component: GeneSetsComponent;
  let fixture: ComponentFixture<GeneSetsComponent>;
  let store: Store;
  const geneSetsServiceMock = new MockGeneSetsService();
  const datasetsTreeServiceMock = new MockDatasetsTreeService();
  const datasetsServiceMock = new DatasetsServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneSetsComponent],
      imports: [
        StoreModule.forRoot({geneSets: geneSetsReducer}),
        HttpClientTestingModule, RouterTestingModule,
        NgbAccordionModule, NgbNavModule,
        CommonModule,
        BrowserModule,
        MatAutocompleteOrigin,
        MatAutocomplete,
        MatAutocompleteTrigger
      ],
      providers: [
        ConfigService, UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: GeneSetsService, useValue: geneSetsServiceMock },
        { provide: DatasetsTreeService, useValue: datasetsTreeServiceMock },
        { provide: DatasetsService, useValue: datasetsServiceMock },
        { provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: '' }
      ], schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneSetsComponent);
    component = fixture.componentInstance;

    // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
    store = TestBed.inject(Store);
    jest.spyOn(store, 'select').mockReturnValue(of());
    jest.spyOn(store, 'dispatch').mockReturnValue(null);

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should change the gene set', () => {
    const geneSetMock1 = new GeneSet('name1', 1, 'desc1', 'download1');
    component.selectedGeneSet = geneSetMock1;
    expect(component.selectedGeneSet).toStrictEqual(GeneSet.fromJson({
      name: 'name1',
      count: 1,
      desc: 'desc1',
      download: 'download1'
    }));

    const geneSetMock2 = new GeneSet('name2', 3, 'desc4', 'download5');
    component.selectedGeneSet = geneSetMock2;
    expect(component.selectedGeneSet).toStrictEqual(GeneSet.fromJson({
      name: 'name2',
      count: 3,
      desc: 'desc4',
      download: 'download5'
    }));
  });

  it('should set and get selectedGeneSetsCollection', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType(
        'datasetId3',
        'datasetName4',
        [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
      ),
      new GeneSetType(
        'datasetId9',
        'datasetName10',
        [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])]
      )
    ]);

    component.selectedGeneSetsCollection = geneSetsCollectionMock1;

    expect(component.selectedGeneSetsCollection).toStrictEqual(GeneSetsCollection.fromJson({
      name: 'name1',
      desc: 'desc2',
      types: [
        new GeneSetType('datasetId3', 'datasetName4', [
          new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])
        ]),
        new GeneSetType('datasetId9', 'datasetName10', [
          new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])
        ])
      ]
    }));
  });

  it('should set and check if selectedGeneType has been set', () => {
    jest.useFakeTimers();

    component.setSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3', true);
    component.setSelectedGeneType('datasetId4', 'personSetCollectionId5', 'geneType6', false);
    jest.advanceTimersByTime(350);

    expect(component.isSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3')).toBe(true);
    expect(component.datasetsList).toStrictEqual(new Set<string>(['datasetId1: personSetCollectionId2: geneType3']));
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['datasetId1']));

    expect(component.isSelectedGeneType('datasetId4', 'personSetCollectionId5', 'geneType6')).toBe(false);
    expect(component.datasetsList).toStrictEqual(new Set<string>(['datasetId1: personSetCollectionId2: geneType3']));
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['datasetId1']));

    component.setSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3', false);
    jest.advanceTimersByTime(350);
    expect(component.isSelectedGeneType('datasetId1', 'personSetCollectionId2', 'geneType3')).toBe(false);
  });

  it('should add type to existing collection of a dataset in current selected types object', () => {
    jest.useFakeTimers();

    component.currentGeneSetsTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism'])
        ])
    ];
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism']);

    component.setSelectedGeneType('deNovo', 'phenotype', 'unaffected', true);
    jest.advanceTimersByTime(350);

    expect(component.currentGeneSetsTypes).toStrictEqual(
      [
        new SelectedDenovoTypes(
          'deNovo',
          [
            new SelectedPersonSetCollections('phenotype', ['autism', 'unaffected'])
          ])
      ]
    );

    expect(component.selectedGeneSet).toBeNull();
    expect(component.searchQuery).toBe('');
    expect(component.datasetsList).toContain('deNovo: phenotype: unaffected');
    expect(component.datasetsList).toContain('deNovo: phenotype: autism');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['deNovo']));
  });

  it('should add type and new collection to dataset in current selected types object', () => {
    jest.useFakeTimers();

    component.currentGeneSetsTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism'])
        ])
    ];
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism']);

    component.setSelectedGeneType('deNovo', 'nonExistingCollection', 'unaffected', true);
    jest.advanceTimersByTime(350);

    expect(component.currentGeneSetsTypes).toStrictEqual(
      [
        new SelectedDenovoTypes(
          'deNovo',
          [
            new SelectedPersonSetCollections('phenotype', ['autism']),
            new SelectedPersonSetCollections('nonExistingCollection', ['unaffected'])
          ]
        )
      ]
    );

    expect(component.selectedGeneSet).toBeNull();
    expect(component.searchQuery).toBe('');
    expect(component.datasetsList).toContain('deNovo: nonExistingCollection: unaffected');
    expect(component.datasetsList).toContain('deNovo: phenotype: autism');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['deNovo']));
  });

  it('should add type and new dataset in current selected types object', () => {
    jest.useFakeTimers();

    component.currentGeneSetsTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism'])
        ])
    ];
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism']);
    component.modifiedDatasetIds = new Set<string>(['deNovo']);

    component.setSelectedGeneType('newDatasetId', 'phenotype', 'unaffected', true);
    jest.advanceTimersByTime(350);

    expect(component.currentGeneSetsTypes).toStrictEqual(
      [
        new SelectedDenovoTypes(
          'deNovo',
          [
            new SelectedPersonSetCollections('phenotype', ['autism']),
          ]
        ),
        new SelectedDenovoTypes(
          'newDatasetId',
          [
            new SelectedPersonSetCollections('phenotype', ['unaffected']),
          ]
        )
      ]
    );

    expect(component.selectedGeneSet).toBeNull();
    expect(component.searchQuery).toBe('');
    expect(component.datasetsList).toContain('newDatasetId: phenotype: unaffected');
    expect(component.datasetsList).toContain('deNovo: phenotype: autism');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['deNovo', 'newDatasetId']));
  });

  it('should remove type from collection of a dataset in current selected types object', () => {
    jest.useFakeTimers();

    component.currentGeneSetsTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism', 'unaffected'])
        ])
    ];
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism', 'deNovo: phenotype: unaffected']);
    component.modifiedDatasetIds = new Set<string>(['deNovo']);

    component.setSelectedGeneType('deNovo', 'phenotype', 'unaffected', false);
    jest.advanceTimersByTime(350);

    expect(component.currentGeneSetsTypes).toStrictEqual(
      [
        new SelectedDenovoTypes(
          'deNovo',
          [
            new SelectedPersonSetCollections('phenotype', ['autism']),
          ]
        )
      ]
    );

    expect(component.selectedGeneSet).toBeNull();
    expect(component.searchQuery).toBe('');
    expect(component.datasetsList).not.toContain('deNovo: phenotype: unaffected');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['deNovo']));
  });

  it('should remove collection of a dataset removing the last type from current selected types object', () => {
    jest.useFakeTimers();

    component.currentGeneSetsTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism']),
          new SelectedPersonSetCollections('16p_status', ['negative'])
        ])
    ];
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism', 'deNovo: 16p_status: negative']);
    component.modifiedDatasetIds = new Set<string>(['deNovo']);

    component.setSelectedGeneType('deNovo', 'phenotype', 'autism', false);
    jest.advanceTimersByTime(350);

    expect(component.currentGeneSetsTypes).toStrictEqual([
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('16p_status', ['negative'])
        ])
    ]);

    expect(component.selectedGeneSet).toBeNull();
    expect(component.searchQuery).toBe('');
    expect(component.datasetsList).toContain('deNovo: 16p_status: negative');
    expect(component.datasetsList).not.toContain('deNovo: phenotype: affected');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['deNovo']));
  });

  it('should remove the only collection of a dataset removing the last type' +
    ' and remove the dataset from current selected types object', () => {
    jest.useFakeTimers();

    component.currentGeneSetsTypes = [
      new SelectedDenovoTypes(
        'deNovo',
        [
          new SelectedPersonSetCollections('phenotype', ['autism'])
        ])
    ];
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism']);
    component.modifiedDatasetIds = new Set<string>(['deNovo']);

    component.setSelectedGeneType('deNovo', 'phenotype', 'autism', false);
    jest.advanceTimersByTime(350);

    expect(component.currentGeneSetsTypes).toStrictEqual([]);

    expect(component.selectedGeneSet).toBeNull();
    expect(component.searchQuery).toBe('');
    expect(component.datasetsList).not.toContain('deNovo: phenotype: affected');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>([]));
  });
  it('should set onSelect', () => {
    const geneSetsCollectionMock1 = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType(
        'datasetId3',
        'datasetName4',
        [new DenovoPersonSetCollection('personSetCollectionId5', 'personSetCollectionName6', [])]
      ),
      new GeneSetType(
        'datasetId9',
        'datasetName10',
        [new DenovoPersonSetCollection('personSetCollectionId11', 'personSetCollectionName12', [])]
      )
    ]);

    component.selectedGeneSetsCollection = geneSetsCollectionMock1;
    const spy = jest.spyOn(component, 'onSearch');

    fixture.detectChanges();

    component.onSelect(new GeneSet('name1', 2, 'desc3', 'download4'));
    expect(component.selectedGeneSet).toStrictEqual(new GeneSet('name1', 2, 'desc3', 'download4'));
    expect(spy).not.toHaveBeenCalledWith();

    component.onSelect(null);
    expect(spy).toHaveBeenCalledWith();
  });

  it('should set onSearch', () => {
    component.selectedGeneSetsCollection = new GeneSetsCollection('name1', 'desc2', [
      new GeneSetType(
        'datasetId1',
        'datasetName2',
        [new DenovoPersonSetCollection('personSetCollectionId3', 'personSetCollectionName4', [])]
      ),
      new GeneSetType(
        'datasetId7',
        'datasetName8',
        [new DenovoPersonSetCollection('personSetCollectionId9', 'personSetCollectionName10', [])]
      ),
    ]);

    component.geneSets = [
      new GeneSet('name13', 14, 'desc15', 'download16'),
      new GeneSet('name17', 18, 'desc19', 'download20')
    ];
    component.searchQuery = 'name15';
    component.onSearch();
    expect(component.searchQuery).toBe('name15');
    expect(component.geneSets).toStrictEqual([]);

    component.geneSets = [
      new GeneSet('name13', 14, 'desc15', 'download16'),
      new GeneSet('name17', 18, 'desc19', 'download20'),
      new GeneSet('name17', 21, 'desc20', 'download21')
    ];
    component.searchQuery = 'name17';
    component.onSearch();
    expect(component.geneSets).toStrictEqual([
      new GeneSet('name17', 18, 'desc19', 'download20'),
      new GeneSet('name17', 21, 'desc20', 'download21')]);
  });

  it('should remove selected types from the list of types displayed in ui', () => {
    component.datasetsList = new Set<string>(['deNovo: phenotype: autism', 'deNovo: 16p_status: negative']);

    const setSelectedGeneTypeSpy = jest.spyOn(component, 'setSelectedGeneType');
    component.removeFromList('deNovo: 16p_status: negative');

    expect(setSelectedGeneTypeSpy).toHaveBeenCalledWith('deNovo', '16p_status', 'negative', false);
  });

  it('should set the selected dataset as an active dataset', () => {
    const datasetNode = new GeneSetTypeNode('datasetId', 'datasetName', [], []);
    expect(component.activeDataset).toBeUndefined();

    component.select(datasetNode);
    expect(component.activeDataset).toBe(datasetNode);
  });

  it('should expand dataset when clicking it in the hierarchy', () => {
    const datasetNodeChild = new GeneSetTypeNode('childStudyId', 'childStudyName', [], []);
    const datasetNode = new GeneSetTypeNode('datasetId', 'datasetName', [], [datasetNodeChild]);
    expect(component.expandedDatasets).toStrictEqual([]);

    component.toggleDatasetCollapse(datasetNode);
    expect(component.expandedDatasets).toStrictEqual([datasetNode]);
  });

  it('should close all inner opened datasets when closing a parent in the hierarchy', () => {
    const datasetNodeChild2 = new GeneSetTypeNode('childStudyId2', 'childStudyName2', [], []);
    const datasetNodeChild1 = new GeneSetTypeNode('childStudyId1', 'childStudyName1', [], [datasetNodeChild2]);
    const datasetNode = new GeneSetTypeNode('datasetId', 'datasetName', [], [datasetNodeChild1]);
    const datasetNodeParallel = new GeneSetTypeNode(
      'parallelDatasetId',
      'parallelDatasetName',
      [],
      [datasetNodeChild1]
    );
    component.expandedDatasets = [datasetNode, datasetNodeChild1, datasetNodeParallel];

    component.toggleDatasetCollapse(datasetNode);
    expect(component.expandedDatasets).toStrictEqual([datasetNodeParallel]);
  });

  it('should create denovo modal hierarchy', () => {
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      datasetHierarchyMock,
      visibleDatasetsMock,
      denovoGeneSetsMock,
      'SSC_genotypes',
      {
        geneSet: null,
        geneSetsCollection: null,
        geneSetsTypes: null,
      }
    ]));

    component.ngOnInit();
    expect(component.denovoDatasetsHierarchy).toStrictEqual(
      [
        new GeneSetTypeNode('SSC_genotypes', 'SSC Genotypes', [new DenovoPersonSetCollection('phenotype', 'phenotype', [
          new PersonSet('autism', 'autism', '#0000'),
          new PersonSet('unaffected', 'unaffected', '#0000'),
        ])], [
          new GeneSetTypeNode(
            'SFARI_SSC_WGS_2', 'SSC NYGC WGS',
            [new DenovoPersonSetCollection('phenotype', 'phenotype', [
              new PersonSet('autism', 'autism', '#0000'),
              new PersonSet('unaffected', 'unaffected', '#0000'),
            ])],
            []
          ),
          new GeneSetTypeNode(
            'SFARI_SSC_WGS_CSHL',
            'SSC CSHL WGS',
            [new DenovoPersonSetCollection('phenotype', 'phenotype', [
              new PersonSet('autism', 'autism', '#0000'),
              new PersonSet('unaffected', 'unaffected', '#0000'),
            ])],
            []),
        ]),
        new GeneSetTypeNode(
          'ssc_rna_seq',
          'SSC LCL RNA Sequencing',
          [new DenovoPersonSetCollection('phenotype', 'phenotype', [
            new PersonSet('autism', 'autism', '#0000'),
            new PersonSet('unaffected', 'unaffected', '#0000'),
          ])],
          []
        ),
      ]
    );

    expect(component.geneSetsCollections).toStrictEqual(geneSetsCollectionMock);
    expect(component.selectedGeneSetsCollection.name).toBe('denovo');
    expect(component.activeDataset.datasetId).toBe('SSC_genotypes');
    expect(component.geneSetsLoaded).toBe(2);
  });

  it('should not create denovo modal hierarchy when datasets hierarchy nodes are invalid', () => {
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      [null],
      visibleDatasetsMock,
      denovoGeneSetsMock,
      'SSC_genotypes',
      {
        geneSet: null,
        geneSetsCollection: null,
        geneSetsTypes: null,
      }
    ]));

    component.ngOnInit();
    expect(component.denovoDatasetsHierarchy).toStrictEqual([]);
  });

  it('should restore gene sets types', () => {
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      datasetHierarchyMock,
      visibleDatasetsMock,
      denovoGeneSetsMock,
      'datasetId',
      {
        geneSet: new GeneSet('geneSet1', 10, 'geneSet1', 'download'),
        geneSetsCollection: new GeneSetsCollection('denovo', 'denovo', []),
        geneSetsTypes: [
          new SelectedDenovoTypes('SFARI_SSC_WGS_CSHL', [
            new SelectedPersonSetCollections('phenotype', ['unaffected'])
          ])
        ]
      }
    ]));

    component.ngOnInit();
    expect(component.selectedGeneSet.name).toBe('geneSet1');
    expect(component.expandedDatasets[0].datasetId).toBe('SSC_genotypes');
    expect(component.datasetsList).toContain('SFARI_SSC_WGS_CSHL: phenotype: unaffected');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['SFARI_SSC_WGS_CSHL']));
  });

  it('should select first person set type from the first dataset as default', () => {
    const rxjs = jest.requireActual<typeof import('rxjs')>('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of([
      datasetHierarchyMock,
      visibleDatasetsMock,
      denovoGeneSetsMock,
      'SSC_genotypes',
      {
        geneSet: null,
        geneSetsCollection: null,
        geneSetsTypes: null
      }
    ]));

    component.ngOnInit();
    expect(component.selectedGeneSet).toBeNull();
    expect(component.activeDataset.datasetId).toBe('SSC_genotypes');
    expect(component.datasetsList).toContain('SSC_genotypes: phenotype: autism');
    expect(component.modifiedDatasetIds).toStrictEqual(new Set<string>(['SSC_genotypes']));
  });
});