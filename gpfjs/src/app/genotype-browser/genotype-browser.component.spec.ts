import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GenotypeBrowserComponent } from './genotype-browser.component';
import { QueryService } from 'app/query/query.service';
import { ConfigService } from 'app/config/config.service';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { APP_BASE_HREF } from '@angular/common';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { UsersService } from 'app/users/users.service';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { RegionsBlockComponent } from 'app/regions-block/regions-block.component';
import { GenotypeBlockComponent } from 'app/genotype-block/genotype-block.component';
import { GenomicScoresBlockComponent } from 'app/genomic-scores-block/genomic-scores-block.component';
import { GenomicScoresBlockService } from 'app/genomic-scores-block/genomic-scores-block.service';
import {
  UniqueFamilyVariantsFilterComponent
} from 'app/unique-family-variants-filter/unique-family-variants-filter.component';
import { SaveQueryComponent } from 'app/save-query/save-query.component';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { EffectTypesComponent } from 'app/effect-types/effect-types.component';
import { GenderComponent } from 'app/gender/gender.component';
import { VariantTypesComponent } from 'app/variant-types/variant-types.component';
import { PresentInChildComponent } from 'app/present-in-child/present-in-child.component';
import { PresentInParentComponent } from 'app/present-in-parent/present-in-parent.component';
import { ErrorsAlertComponent } from 'app/errors-alert/errors-alert.component';
import { CheckboxListComponent, DisplayNamePipe } from 'app/checkbox-list/checkbox-list.component';
import { EffecttypesColumnComponent } from 'app/effect-types/effect-types-column.component';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PersonFiltersBlockComponent } from 'app/person-filters-block/person-filters-block.component';
import { FormsModule } from '@angular/forms';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { of } from 'rxjs/internal/observable/of';
import { HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs/internal/Observable';
import { NavigationStart, Router, Event } from '@angular/router';
import { Subject } from 'rxjs/internal/Subject';
import {
  Column, Dataset, GenotypeBrowser, PersonFilter,
  PersonSet, PersonSetCollection, PersonSetCollections } from 'app/datasets/datasets';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { Store, StoreModule } from '@ngrx/store';
import { PresentInParent, presentInParentReducer } from 'app/present-in-parent/present-in-parent.state';
import { PedigreeSelector, pedigreeSelectorReducer } from 'app/pedigree-selector/pedigree-selector.state';
import { FamilyTags } from 'app/family-tags/family-tags';
import { GeneSet, GeneSetsCollection } from 'app/gene-sets/gene-sets';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { familyIdsReducer } from 'app/family-ids/family-ids.state';
import { familyTagsReducer } from 'app/family-tags/family-tags.state';
import { personFiltersReducer } from 'app/person-filters/person-filters.state';
import { geneSymbolsReducer } from 'app/gene-symbols/gene-symbols.state';
import { geneSetsReducer } from 'app/gene-sets/gene-sets.state';
import { geneScoresReducer } from 'app/gene-scores/gene-scores.state';
import { regionsFiltersReducer } from 'app/regions-filter/regions-filter.state';
import { genomicScoresReducer } from 'app/genomic-scores-block/genomic-scores-block.state';
import { personIdsReducer } from 'app/person-ids/person-ids.state';
import { uniqueFamilyVariantsFilterReducer }
  from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import { studyFiltersReducer } from 'app/study-filters/study-filters.state';
import { errorsReducer } from 'app/common/errors.state';
import { studyTypesReducer } from 'app/study-types/study-types.state';
import { presentInChildReducer } from 'app/present-in-child/present-in-child.state';
import { inheritanceTypesReducer } from 'app/inheritancetypes/inheritancetypes.state';
import { gendersReducer } from 'app/gender/gender.state';
import { effectTypesReducer } from 'app/effect-types/effect-types.state';
import { variantTypesReducer } from 'app/variant-types/variant-types.state';
import { datasetIdReducer } from 'app/datasets/datasets.state';

/* eslint-disable */
const genotypeMock = GenotypeBrowser.fromJson({
  has_pedigree_selector: false,
  has_present_in_child: true,
  has_present_in_parent: false,
  has_present_in_role: false,
  has_family_filters: true,
  has_family_structure_filter: false,
  has_person_filters: true,
  has_study_filters: false,
  has_study_types: false,
  table_columns: [
    {
      name: 'name1',
      source: 'source1',
      format: 'format1'
    },
    {
      name: 'name2',
      source: 'source2',
      format: 'format2'
    }
  ],
  person_filters: [
    {
      name: 'personFilter1',
      from: 'string1',
      source: 'source1',
      source_type: 'sourceType1',
      filter_type: 'filterType1',
      role: 'role1',
    },
    {
      name: 'personFilter2',
      from: 'string2',
      source: 'source2',
      source_type: 'sourceType2',
      filter_type: 'filterType2',
      role: 'role2',
    }
  ],
  family_filters: [
    {
      name: 'familyFilter3',
      from: 'string3',
      source: 'source3',
      source_type: 'sourceType3',
      filter_type: 'filterType3',
      role: 'role3',
    },
    {
      name: 'familyFilter4',
      from: 'string4',
      source: 'source4',
      source_type: 'sourceType4',
      filter_type: 'filterType4',
      role: 'role4',
    }
  ],
  inheritance_type_filter: ['inheritance', 'string1'],
  selected_inheritance_type_filter_values: ['selectedInheritance', 'string2'],
  variant_types: ['variant', 'string3'],
  selected_variant_types: ['selectedVariant', 'string1'],
  max_variants_count: 5,
});
/* eslint-enable */

const genotypeBrowserStateResult = {
  variantTypes: ['ins'],
  effectTypes: ['missense'],
  genders: ['male'],
  inheritanceTypeFilter: [],
  presentInChild: ['sibling only'],
  studyTypes: ['studyType'],
  familyIds: ['familyId1'],
  geneSymbols: ['chd8'],
  regions: ['regionFrom-regionTo'],
  genomicScores: [{
    metric: 'phylop100way',
    rangeStart: -14.9,
    rangeEnd: 4.899999999999999
  }],
  personIds: ['personId1'],
  studyFilters: ['SD_Chung2015CHD_liftover'],
  uniqueFamilyVariants: false,
  personSetCollection: {
    id: 'personSetCollection',
    checkedValues: ['checkedValue1']
  },
  tagIntersection: false,
  selectedFamilyTags: ['tag1'],
  deselectedFamilyTags: ['tag2'],
  familyFilters: [{
    id: 'Mother Race',
    sourceType: 'categorical',
    role: 'mom',
    from: 'phenodb',
    selection: {
      selection: [
        'african-amer'
      ]
    },
    source: 'ssc_commonly_used.race_parents'
  }],
  personFilters: [{
    id: 'Biospecimen wb_dna',
    sourceType: 'categorical',
    from: 'phenodb',
    selection: {
      selection: [
        0
      ]
    },
    source: 'ssc_biospecimen.wb_dna'
  }],
  geneSet: {
    geneSet: 'LGDs',
    geneSetsCollection: 'denovo',
    geneSetsTypes: [
      {
        datasetId: 'sequencing_de_novo',
        collections: [
          {
            personSetId: 'phenotype',
            types: [
              'developmental_disorder'
            ]
          }
        ]
      }
    ]
  },
  geneScores: {
    score: 'LGD_rank',
    rangeStart: 3434.5466666666666,
    rangeEnd: 16923.48
  },
  presentInParent: {
    presentInParent: ['neither'],
    rarity: {
      ultraRare: false,
      minFreq: 0,
      maxFreq: 1,
    }
  },
};

const allStatesMock = [
  ['ins'],
  ['missense'],
  ['male'],
  [],
  ['sibling only'],
  { presentInParent: ['neither'],
    rarity: {
      rarityType: 'rare',
      rarityIntervalStart: 0,
      rarityIntervalEnd: 1,
    }},
  ['studyType'],
  {
    id: 'personSetCollection',
    checkedValues: ['checkedValue1']
  } as PedigreeSelector,
  ['familyId1'],
  {
    selectedFamilyTags: ['tag1'],
    deselectedFamilyTags: ['tag2'],
    tagIntersection: false,
  } as FamilyTags,
  {
    personFilters: [{
      id: 'Biospecimen wb_dna',
      sourceType: 'categorical',
      from: 'phenodb',
      selection: {
        selection: [
          0
        ]
      },
      source: 'ssc_biospecimen.wb_dna'
    }],
    familyFilters: [{
      id: 'Mother Race',
      sourceType: 'categorical',
      role: 'mom',
      from: 'phenodb',
      selection: {
        selection: [
          'african-amer'
        ]
      },
      source: 'ssc_commonly_used.race_parents'
    }]
  },
  ['chd8'],
  {
    geneSet: new GeneSet('LGDs', 0, '', ''),
    geneSetsCollection: new GeneSetsCollection('denovo', '', []),
    geneSetsTypes: [
      {
        datasetId: 'sequencing_de_novo',
        collections: [
          {
            personSetId: 'phenotype',
            types: [
              'developmental_disorder'
            ]
          }
        ]
      }
    ]
  },
  {
    score: 'LGD_rank',
    rangeStart: 3434.5466666666666,
    rangeEnd: 16923.48
  },
  ['regionFrom-regionTo'],
  [
    {
      metric: 'phylop100way',
      rangeStart: -14.9,
      rangeEnd: 4.899999999999999
    }
  ],
  ['personId1'],
  false,
  ['SD_Chung2015CHD_liftover']
];

const mockDataset = new Dataset(
  'testDatasetId',
  'testDataset',
  [], true, [], [], [], '', true, true, true, true, null,
  genotypeMock, null, [], null, null, '', null
);
class MockDatasetsService {
  public getDataset(datasetId: string): Observable<Dataset> {
    if (datasetId === 'testDatasetId') {
      return of(mockDataset);
    }
    return of(null);
  }
}
class MockQueryService {
  public streamingSubject = new Subject();
  public streamingFinishedSubject = new Subject();
  public downloadVariants(): Observable<HttpResponse<Blob>> {
    return of([] as any) as Observable<HttpResponse<Blob>>;
  }

  public cancelStreamPost(): void {
    return null;
  }

  public getGenotypePreviewVariantsByFilter(
    dataset: Dataset,
    filter,
    maxVariantsCount: number = 1001,
    callback?: () => void
  ): GenotypePreviewVariantsArray {
    return new GenotypePreviewVariantsArray();
  }
}


describe('GenotypeBrowserComponent', () => {
  let component: GenotypeBrowserComponent;
  let fixture: ComponentFixture<GenotypeBrowserComponent>;
  const queryService = new MockQueryService();
  const mockDatasetsService = new MockDatasetsService();
  let loadingService: FullscreenLoadingService;
  let store: Store;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        GenotypeBrowserComponent,
        GenotypeBlockComponent,
        GenomicScoresBlockComponent,
        SaveQueryComponent,
        PresentInChildComponent,
        PresentInParentComponent,
        ErrorsAlertComponent,
        CheckboxListComponent,
        EffecttypesColumnComponent,
        FamilyFiltersBlockComponent,
        PersonFiltersBlockComponent,
        DisplayNamePipe
      ],
      providers: [
        {provide: QueryService, useValue: queryService},
        ConfigService,
        FullscreenLoadingService,
        UsersService,
        VariantReportsService,
        GenomicScoresBlockService,
        { provide: DatasetsService, useValue: mockDatasetsService },
        UniqueFamilyVariantsFilterComponent,
        EffectTypesComponent,
        GenderComponent,
        VariantTypesComponent,
        GenesBlockComponent,
        RegionsBlockComponent,
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [
        HttpClientTestingModule, RouterTestingModule, NgbNavModule, FormsModule,
        StoreModule.forRoot({
          familyIds: familyIdsReducer,
          familyTags: familyTagsReducer,
          personFilters: personFiltersReducer,
          geneSymbols: geneSymbolsReducer,
          geneSets: geneSetsReducer,
          geneScores: geneScoresReducer,
          regionsFilter: regionsFiltersReducer,
          genomicScores: genomicScoresReducer,
          personIds: personIdsReducer,
          uniqueFamilyVariantsFilter: uniqueFamilyVariantsFilterReducer,
          studyFilters: studyFiltersReducer,
          errors: errorsReducer,
          pedigreeSelector: pedigreeSelectorReducer,
          studyTypes: studyTypesReducer,
          presentInParent: presentInParentReducer,
          presentInChild: presentInChildReducer,
          inheritanceTypes: inheritanceTypesReducer,
          genders: gendersReducer,
          effectTypes: effectTypesReducer,
          variantTypes: variantTypesReducer,
          datasetId: datasetIdReducer,
        }),
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();
    fixture = TestBed.createComponent(GenotypeBrowserComponent);
    component = fixture.componentInstance;
    loadingService = TestBed.inject(FullscreenLoadingService);

    store = TestBed.inject(Store);

    fixture.detectChanges();
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should cancel queries on router change', () => {
    const stopSpy = jest.spyOn(loadingService, 'setLoadingStop');
    const cancelSpy = jest.spyOn(queryService, 'cancelStreamPost');
    const router = TestBed.inject(Router);

    (router.events as Subject<Event>).next(new NavigationStart(1, 'start'));

    expect(stopSpy).toHaveBeenCalledTimes(1);
    expect(cancelSpy).toHaveBeenCalledTimes(1);
  });

  it('should create selected dataset by getting the id from state', () => {
    const mockDatasetsServiceSpy = jest.spyOn(mockDatasetsService, 'getDataset');
    jest.spyOn(store, 'select').mockReturnValueOnce(of('testDatasetId'));

    component.ngOnInit();
    expect(mockDatasetsServiceSpy).toHaveBeenCalledWith('testDatasetId');
    expect(component.selectedDataset).toStrictEqual(mockDataset);

    component.selectedDataset = undefined;

    jest.spyOn(store, 'select').mockReturnValueOnce(of(null));

    component.ngOnInit();
    expect(mockDatasetsServiceSpy).toHaveBeenCalledWith(null);
    expect(component.selectedDataset).toBeUndefined();
  });

  it('should create genotype browser state with rare rarity', () => {
    jest.clearAllMocks();
    const rxjs = jest.requireActual('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(allStatesMock));
    component.ngOnInit();

    expect(component.genotypeBrowserState).toStrictEqual(genotypeBrowserStateResult);
    expect(component.genotypePreviewVariantsArray).toBeNull();
  });

  it('should create genotype browser state with interval rarity', () => {
    jest.clearAllMocks();
    const rxjs = jest.requireActual('rxjs');
    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(allStatesMock));

    allStatesMock[5] = {
      presentInParent: ['neither'],
      rarity: {
        rarityType: 'interval',
        rarityIntervalStart: 0,
        rarityIntervalEnd: 1,
      }} as PresentInParent;

    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(allStatesMock));
    component.ngOnInit();
    expect(component.genotypeBrowserState).toStrictEqual(genotypeBrowserStateResult);
  });

  it('should get genotype browser state with ultra rare rarity', () => {
    jest.clearAllMocks();
    const rxjs = jest.requireActual('rxjs');

    allStatesMock[5] = {
      presentInParent: ['neither'],
      rarity: {
        rarityType: 'ultraRare'
      }} as PresentInParent;

    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(allStatesMock));
    component.ngOnInit();

    delete genotypeBrowserStateResult.presentInParent.rarity.maxFreq;
    delete genotypeBrowserStateResult.presentInParent.rarity.minFreq;

    genotypeBrowserStateResult.presentInParent.rarity.ultraRare = true;
    expect(component.genotypeBrowserState).toStrictEqual(genotypeBrowserStateResult);
    expect(component.genotypePreviewVariantsArray).toBeNull();
  });

  it('should create genotype browser empty state when all component states are empty', () => {
    jest.clearAllMocks();
    const rxjs = jest.requireActual('rxjs');

    const emptyStatesMock = [
      [],
      [],
      [],
      [],
      [],
      { presentInParent: [],
        rarity: {}},
      [],
      {},
      [],
      {
        selectedFamilyTags: [],
        deselectedFamilyTags: [],
        tagIntersection: true,
      } as FamilyTags,
      {
        personFilters: [],
        familyFilters: []
      },
      [],
      {
        geneSet: null,
        geneSetsCollection: null,
        geneSetsTypes: []
      },
      {
        score: null,
        rangeStart: 3434.5466666666666,
        rangeEnd: 16923.48
      },
      [],
      [],
      [],
      false,
      []
    ];

    jest.spyOn(rxjs, 'combineLatest').mockReturnValueOnce(of(emptyStatesMock));
    component.ngOnInit();
    expect(component.genotypeBrowserState).toStrictEqual(
      {
        inheritanceTypeFilter: [],
        genomicScores: [],
        studyFilters: [],
        uniqueFamilyVariants: false,
        personSetCollection: { }
      }
    );
  });

  it('should test submitting query', () => {
    component.selectedDataset = new Dataset(
      'testDatasetId',
      null, ['id1', 'parent2'], null, null, null, null, null,
      null, null, null, null, null,
      new GenotypeBrowser(
        false,
        false,
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
        [],
        [
          new PersonFilter('familyFilter3', 'string3', 'source3', 'sourceType3', 'filterType3', 'role3'),
          new PersonFilter('familyFilter4', 'string4', 'source4', 'sourceType4', 'filterType4', 'role4')
        ],
        ['inheritance', 'string1'],
        ['selectedInheritance', 'string2'],
        ['variant', 'string3'],
        ['selectedVariant', 'string1'],
        5
      ), new PersonSetCollections(
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
      ), null, null, null, null, null
    );

    component.loadingFinished = true;
    component.showTable = true;
    component.variantsCountDisplay = '';
    // const setLoadingStartSpy = jest.spyOn(component, 'setLoadingStart');
    component.submitQuery();

    expect(component.loadingFinished).toBe(false);
    expect(component.showTable).toBe(false);
    expect(component.variantsCountDisplay).toBe('Loading variants...');
    expect(component.genotypePreviewVariantsArray).toStrictEqual(new GenotypePreviewVariantsArray());
    expect(component.genotypeBrowserState['datasetId']).toBe('testDatasetId');
  });

  it('should test download', () => {
    const mockEvent = {
      target: {
        queryData: {
          value: ''
        },
        submit: jest.fn()
      }
    };
    component.genotypeBrowserState = {};
    component.selectedDataset = mockDataset;

    component.onSubmit(mockEvent);
    expect(mockEvent.target.queryData.value).toStrictEqual(JSON.stringify({
      datasetId: component.selectedDataset.id,
      download: true,
    }));
    expect(mockEvent.target.submit).toHaveBeenCalledTimes(1);
  });
});
