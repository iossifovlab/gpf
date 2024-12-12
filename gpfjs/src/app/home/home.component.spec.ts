import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';

import { HomeComponent } from './home.component';
import { HttpClient, HttpHandler } from '@angular/common/http';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { APP_BASE_HREF } from '@angular/common';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { Observable, of, throwError } from 'rxjs';
import { GeneService } from 'app/gene-browser/gene.service';
import {
  MatAutocompleteOrigin,
  MatAutocomplete,
  MatAutocompleteTrigger,
  MAT_AUTOCOMPLETE_SCROLL_STRATEGY } from '@angular/material/autocomplete';
import { GeneProfilesSingleViewConfig } from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { StoreModule } from '@ngrx/store';
import { DatasetHierarchy } from 'app/datasets/datasets';
import { GeneProfilesService } from 'app/gene-profiles-block/gene-profiles.service';
import { GeneProfilesTableService } from 'app/gene-profiles-table/gene-profiles-table.service';
import { InstanceService } from 'app/instance.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';

const config = {
  geneLinkTemplates: [
    {
      name: 'link1',
      url: 'url1'
    },
    {
      name: 'link2',
      url: 'url2'
    }
  ],
  shown: [],
  defaultDataset: 'mockDataset',
  description: 'mock description',
  geneSets: [
    {
      category: 'autism_gene_sets',
      displayName: 'Autism Gene Sets',
      defaultVisible: true,
      sets: [
        { setId: 'SFARI ALL', defaultVisible: true, collectionId: 'sfari', meta: null }
      ]
    }
  ],
  genomicScores: [
    {
      category: 'autism_scores',
      defaultVisible: true,
      displayName: 'Autism Scores',
      scores: [
        { format: '%s', defaultVisible: true, scoreName: 'SFARI gene score', meta: null }
      ]
    }
  ],
  datasets: [
    {
      defaultVisible: true,
      displayName: 'Sequencing de Novo',
      id: 'sequencing_de_novo',
      meta: null,
      shown: [],
      personSets: [
        {
          id: 'autism',
          shown: [],
          defaultVisible: true,
          displayName: 'autism',
          collectionId: 'phenotype',
          description: '',
          childrenCount: 21775,
          statistics: [
            {
              id: 'denovo_lgds',
              description: 'de Novo LGDs',
              displayName: 'dn LGDs',
              effects: [
                'LGDs'
              ],
              category: 'denovo',
              defaultVisible: true,
              scores: [],
              variantTypes: []
            }
          ]
        }
      ],
      statistics: []
    }
  ],
  order: [
    { section: null, id: 'autism_gene_sets_rank' },
    { section: 'genomicScores', id: 'autism_scores' },
    { section: 'datasets', id: 'sequencing_de_novo' }
  ],
  pageSize: 5
};
class MockGeneService {
  public getGene(): Observable<Record<string, unknown>> {
    return of(
      {
        geneSymbol: 'CHD8',
        collapsedTranscripts: [{
          start: 1,
          stop: 2
        }],
        getRegionString: () => ''
      });
  }
}

const datasetsHierarchy = [
  new DatasetHierarchy('d1', 'dataset1Name', true, [
    new DatasetHierarchy('d1Inner', 'dataset1InnerName', true, [])
  ]),
  new DatasetHierarchy('d2', 'dataset2Name', true, null),
  new DatasetHierarchy('d3', 'dataset3Name', true, [
    new DatasetHierarchy('d3Inner1', 'dataset3InnerName1', true, []),
    new DatasetHierarchy('d3Inner2', 'dataset3InnerName2', true, [
      new DatasetHierarchy('d3InnerInner1', 'dataset3InnerInnerName1', true, []),
      new DatasetHierarchy('d3InnerInner2', 'dataset3InnerInnerName2', true, []),
    ])

  ]),
];
class MockDatasetsTreeService {
  public getDatasetHierarchy(): Observable<DatasetHierarchy[]> {
    return of(datasetsHierarchy);
  }
}

class MockDatasetsService {
  public getVisibleDatasets(): Observable<string[]> {
    return of(['d1', 'd1Inner']);
  }

  public getDatasetDescription(dataseId: string): Observable<string> {
    if (dataseId === 'd1') {
      return of('d1 description');
    } else if (dataseId === 'd1Inner') {
      return of('d1Inner description');
    }
    return of('');
  }
}

class MockInstanceService {
  public getGpfVersion(): Observable<string> {
    return of('version 1');
  }

  public writeHomeDescription(desc: string): Observable<object> {
    return of({ content: desc });
  }

  public getHomeDescription(): Observable<object> {
    return of({content: 'Home page description'});
  }
}

class MockGeneProfilesService {
  public getConfig(): Observable<GeneProfilesSingleViewConfig> {
    return of(config);
  }
}

class MockGeneProfilesTableService {
  public getGeneSymbols(page: number, searchString: string): Observable<string[]> {
    if (searchString === 'searchValue') {
      return of(['searchResult']);
    }
    return of([] as string[]);
  }
}

describe('HomeComponent', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;
  const mockGeneService = new MockGeneService();
  const mockDatasetsTreeService = new MockDatasetsTreeService();
  const mockDatasetsService = new MockDatasetsService();
  const mockInstanceService = new MockInstanceService();
  const mockGeneProfilesService = new MockGeneProfilesService();
  const mockGeneProfilesTableService = new MockGeneProfilesTableService();

  beforeEach(async() => {
    await TestBed.configureTestingModule({
      declarations: [HomeComponent],
      providers: [
        HttpClient,
        HttpHandler,
        ConfigService,
        UsersService,
        { provide: APP_BASE_HREF, useValue: '' },
        { provide: GeneService, useValue: mockGeneService },
        { provide: MAT_AUTOCOMPLETE_SCROLL_STRATEGY, useValue: ''},
        { provide: DatasetsTreeService, useValue: mockDatasetsTreeService },
        { provide: DatasetsService, useValue: mockDatasetsService },
        { provide: InstanceService, useValue: mockInstanceService },
        { provide: GeneProfilesService, useValue: mockGeneProfilesService },
        { provide: GeneProfilesTableService, useValue: mockGeneProfilesTableService },

      ],
      imports: [StoreModule.forRoot({}), MatAutocompleteOrigin, MatAutocomplete, MatAutocompleteTrigger],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should set search results when searching gene', fakeAsync(() => {
    const getGeneSymbolsSpy = jest.spyOn(mockGeneProfilesTableService, 'getGeneSymbols');

    component.ngOnInit();

    component.searchBoxInput$.next('searchValue');
    tick(250);
    expect(getGeneSymbolsSpy).toHaveBeenCalledWith(1, 'searchValue');
    expect(component.geneSymbolSuggestions).toStrictEqual(['searchResult']);

    component.searchBoxInput$.next('');
    tick(250);
    expect(component.geneSymbolSuggestions).toStrictEqual([]);
  }));

  it('should set dataset hierarchy', () => {
    const getDatasetHierarchySpy = jest.spyOn(mockDatasetsTreeService, 'getDatasetHierarchy');
    const getVisibleDatasetsSpy = jest.spyOn(mockDatasetsService, 'getVisibleDatasets');
    const collectAllStudiesSpy = jest.spyOn(component, 'collectAllStudies');
    const attachDatasetDescriptionSpy = jest.spyOn(component, 'attachDatasetDescription');

    component.ngOnInit();

    expect(getDatasetHierarchySpy).toHaveBeenCalledWith();
    expect(getVisibleDatasetsSpy).toHaveBeenCalledWith();
    expect(collectAllStudiesSpy).toHaveBeenCalledTimes(8);
    expect(attachDatasetDescriptionSpy).toHaveBeenCalledTimes(8);

    expect(component.content).toBe(datasetsHierarchy);
    expect(component.visibleDatasets).toStrictEqual(['d1', 'd1Inner']);
    expect(component.datasets).toStrictEqual(['d1', 'd1Inner']);
  });

  it('should set other data', () => {
    const getGpfVersionSpy = jest.spyOn(mockInstanceService, 'getGpfVersion');
    const getHomeDescriptionSpy = jest.spyOn(mockInstanceService, 'getHomeDescription');
    const getConfigSpy = jest.spyOn(mockGeneProfilesService, 'getConfig');

    component.ngOnInit();

    expect(getGpfVersionSpy).toHaveBeenCalledTimes(1);
    expect(getHomeDescriptionSpy).toHaveBeenCalledTimes(1);
    expect(getConfigSpy).toHaveBeenCalledTimes(1);

    expect(component.gpfVersion).toBe('version 1');
    expect(component.geneProfilesConfig).toStrictEqual(config);
    expect(component.homeDescription).toBe('Home page description');
  });

  it('should open sinle view', () => {
    component.loadingFinished = true;
    component.content = [];
    component.geneProfilesConfig = new GeneProfilesSingleViewConfig();
    fixture.detectChanges();

    let geneSymbols = 'CHD8';
    component.openSingleView(geneSymbols);
    expect(component.geneSymbol).toBe('CHD8');

    geneSymbols = '  CHD8 ';
    component.openSingleView(geneSymbols);
    expect(component.geneSymbol).toBe('CHD8');

    geneSymbols = 'chd8';
    component.openSingleView(geneSymbols);
    expect(component.geneSymbol).toBe('CHD8');
  });

  it('should not open sinle view', () => {
    component.loadingFinished = true;
    component.content = [];
    component.geneProfilesConfig = new GeneProfilesSingleViewConfig();
    const getGeneSpy = jest.spyOn(mockGeneService, 'getGene');

    fixture.detectChanges();

    component.openSingleView('  ');
    expect(getGeneSpy).toHaveBeenCalledTimes(0);
  });

  it('should show error message when searching gene', () => {
    component.showError = true;

    component.loadingFinished = true;
    component.content = [];
    component.geneProfilesConfig = new GeneProfilesSingleViewConfig();
    fixture.detectChanges();

    let geneSymbols = '   ';
    component.openSingleView(geneSymbols);
    expect(component.geneSymbol).toBe('');

    jest.spyOn(mockGeneService, 'getGene').mockImplementation(() => throwError(() => new Error()));

    geneSymbols = 'CHD';
    component.showError = false;
    component.openSingleView(geneSymbols);
    expect(component.showError).toBe(true);
  });

  it('should get first parapraph of description when title and description are separated by new line', () => {
    const desc = '## SSC CSHL WGS\n' +
    '*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.' +
    '\n\n' +
    '### Disclaimer' +
    '\n\n' +
    'The use of the Simons Simplex and Simons Searchlight Collections is limited to' +
    'projects that advance the study of autism and related developmental disorders.' +
    'Questions on consents for the Simons Simplex Collection and the Simons' +
    'Searchlight should be directed to collections@sfari.org.';

    const result = component.getFirstParagraph(desc);
    expect(result).toBe('*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.');
  });

  it('should get first parapraph of description when title and description are separated by empty line', () => {
    const desc = '## SSC CSHL WGS\n\n' +
    '*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.' +
    '\n\n' +
    '### Disclaimer' +
    '\n\n' +
    'The use of the Simons Simplex and Simons Searchlight Collections is limited to' +
    'projects that advance the study of autism and related developmental disorders.' +
    'Questions on consents for the Simons Simplex Collection and the Simons' +
    'Searchlight should be directed to collections@sfari.org.';

    const result = component.getFirstParagraph(desc);
    expect(result).toBe('*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.');
  });

  it('should get first parapraph of description when there is no title', () => {
    const desc =
    '*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.' +
    '\n\n' +
    '### Disclaimer' +
    '\n\n' +
    'The use of the Simons Simplex and Simons Searchlight Collections is limited to' +
    'projects that advance the study of autism and related developmental disorders.' +
    'Questions on consents for the Simons Simplex Collection and the Simons' +
    'Searchlight should be directed to collections@sfari.org.';

    const result = component.getFirstParagraph(desc);
    expect(result).toBe('*De novo* and transmitted substitutions and indel calls generated by the' +
    'Iossifov lab from the whole-genome sequencing from 2,379 SSC families.' +
    'NYGC generated the whole-genome data from DNA extracted from whole blood.');
  });

  it('should reset', () => {
    component.geneSymbol = 'chd8';
    component.showError = true;
    component.geneSymbolSuggestions = ['chd8'];

    component.reset();

    expect(component.geneSymbol).toBe('');
    expect(component.showError).toBe(false);
    expect(component.geneSymbolSuggestions).toStrictEqual([]);
  });

  it('should attach dataset descriptions', () => {
    const getFirstParagraphSpy = jest.spyOn(component, 'getFirstParagraph');
    const getDatasetDescriptionSpy = jest.spyOn(mockDatasetsService, 'getDatasetDescription');

    component.attachDatasetDescription(datasetsHierarchy[0]);

    expect(getDatasetDescriptionSpy).toHaveBeenCalledWith('d1');
    expect(getDatasetDescriptionSpy).toHaveBeenCalledWith('d1Inner');
    expect(getFirstParagraphSpy).toHaveBeenCalledTimes(2);
    expect(datasetsHierarchy[0].description).toBe('d1 description');
    expect(datasetsHierarchy[0].children[0].description).toBe('d1Inner description');
    expect(component.studiesLoaded).toBe(2);
    expect(component.loadingFinished).toBe(false);

    component.allStudies = new Set(['d1', 'd1Inner', 'd2']);
    component.attachDatasetDescription(datasetsHierarchy[1]);

    expect(datasetsHierarchy[1].description).toBeUndefined();
    expect(component.studiesLoaded).toBe(3);
    expect(component.loadingFinished).toBe(true);
  });


  it('should collect all studies', () => {
    component.collectAllStudies(datasetsHierarchy[1]);
    expect(component.allStudies).toStrictEqual(new Set(['d2']));

    component.collectAllStudies(datasetsHierarchy[2]);
    expect(component.allStudies).toStrictEqual(
      new Set(['d2', 'd3', 'd3Inner1', 'd3Inner2', 'd3InnerInner1', 'd3InnerInner2'])
    );
  });

  it('should check if dataset has visible children', () => {
    component.visibleDatasets = ['d2'];
    let result = component.datasetHasVisibleChildren(datasetsHierarchy);
    expect(result).toBe(true);

    result = component.datasetHasVisibleChildren(datasetsHierarchy[0].children);
    expect(result).toBe(false);

    result = component.datasetHasVisibleChildren(datasetsHierarchy[1].children);
    expect(result).toBe(false);
  });

  it('should expand and collapse dataset', () => {
    const findAllByKeySpy = jest.spyOn(component, 'findAllByKey');
    component.visibleDatasets = ['d3'];
    component.datasets = ['d3', 'd3Inner1', 'd3Inner2', 'd3InnerInner1', 'd3InnerInner2'];

    component.toggleDatasetCollapse(datasetsHierarchy[0]);
    expect(findAllByKeySpy).toHaveBeenCalledTimes(0);

    component.toggleDatasetCollapse(datasetsHierarchy[2]);
    expect(findAllByKeySpy).toHaveBeenCalledWith(datasetsHierarchy[2].children, 'id');
    expect(component.datasets).toStrictEqual(['d3']);

    component.datasets = ['d3'];
    component.visibleDatasets = ['d3', 'd3Inner1', 'd3Inner2', 'd3InnerInner1', 'd3InnerInner2'];
    component.toggleDatasetCollapse(datasetsHierarchy[2]);
    expect(component.datasets).toStrictEqual(['d3', 'd3Inner1', 'd3Inner2']);
  });

  it('should get dataset and its children values by property', () => {
    let result = component.findAllByKey(datasetsHierarchy, 'id');
    expect(result).toStrictEqual(
      ['d1', 'd1Inner', 'd2', 'd3', 'd3Inner1', 'd3Inner2', 'd3InnerInner1', 'd3InnerInner2']
    );

    result = component.findAllByKey(datasetsHierarchy[2].children[1], 'name');
    expect(result).toStrictEqual(
      ['dataset3InnerName2', 'dataset3InnerInnerName1', 'dataset3InnerInnerName2']
    );
  });

  it('should write description', () => {
    const desc = 'new home page description';
    const writeDescriptionSpy = jest.spyOn(mockInstanceService, 'writeHomeDescription');
    const getDescriptionSpy = jest.spyOn(mockInstanceService, 'getHomeDescription')
      .mockReturnValueOnce(of({content: desc}));

    component.writeDescription(desc);
    expect(writeDescriptionSpy).toHaveBeenCalledWith(desc);
    expect(getDescriptionSpy).toHaveBeenCalledWith();
    expect(component.homeDescription).toBe('new home page description');
  });
});
