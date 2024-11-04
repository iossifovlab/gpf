import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { GeneScoresService } from 'app/gene-scores/gene-scores.service';
import { UsersService } from 'app/users/users.service';
import { Observable, of, throwError } from 'rxjs';
import { GeneProfileSingleViewComponent } from './gene-profiles-single-view.component';
import { QueryService } from 'app/query/query.service';
import { APP_BASE_HREF } from '@angular/common';
import { Store, StoreModule } from '@ngrx/store';
import {
  GeneProfilesDatasetPersonSet,
  GeneProfilesDatasetStatistic,
  GeneProfilesGenomicScores,
  GeneProfilesGenomicScoreWithValue } from './gene-profiles-single-view';
import { setEffectTypes } from 'app/effect-types/effect-types.state';
import { setGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { setPresentInChild } from 'app/present-in-child/present-in-child.state';
import { setPresentInParent } from 'app/present-in-parent/present-in-parent.state';
import { setVariantTypes } from 'app/variant-types/variant-types.state';
import { setPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { setGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { setStudyTypes } from 'app/study-types/study-types.state';
import { GenomicScore } from 'app/genotype-browser/genotype-browser';
import { selectGeneProfiles, setGeneProfilesOpenedTabs } from 'app/gene-profiles-table/gene-profiles-table.state';

class QueryServiceMock {
  public saveQuery(state: object, tool: string): Observable<object> {
    return of({});
  }

  public getLoadUrlFromResponse(obj: object): string {
    return 'url';
  }
}

describe('GeneProfileSingleViewComponent', () => {
  let component: GeneProfileSingleViewComponent;
  let fixture: ComponentFixture<GeneProfileSingleViewComponent>;
  let store: Store;
  const queryServiceMock = new QueryServiceMock();

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneProfileSingleViewComponent],
      providers: [
        ConfigService, GeneScoresService, DatasetsService,
        UsersService,
        {provide: QueryService, useValue: queryServiceMock },
        { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, StoreModule.forRoot({})]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneProfileSingleViewComponent);
    component = fixture.componentInstance;
    store = TestBed.inject(Store);
    component.config = {geneSets: ['mockGeneSet']} as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    (component as any).geneSymbol = 'mockGeneSymbol';
    const getGeneSpy = jest.spyOn(component['geneProfilesService'], 'getGene');
    const fakeScores1 = [{id: 'fakeScore1', value: 1, format: ''}];
    const fakeScores2 = [{id: 'fakeScore2', value: 1, format: ''}];
    const mockGenomicScores = [
      {id: 'fakeGenomicScore1', scores: fakeScores1},
      {id: 'fakeGenomicScore2', scores: fakeScores2}
    ];

    let geneMock = of({
      genomicScores: mockGenomicScores,
      geneSets: ['test1', 'test2', 'test3_sfari']
    } as any);
    getGeneSpy.mockReturnValue(geneMock);

    const getGeneScoresSpy = jest.spyOn(component['geneScoresService'], 'getGeneScores');
    getGeneScoresSpy.mockReturnValue(of('fakeScore' as any));

    expect(component.isGeneInSFARI).toBeFalsy();
    component.ngOnInit();
    expect(component['gene$']).toStrictEqual(geneMock);
    expect(component.isGeneInSFARI).toBeTruthy();
    expect(getGeneSpy).toHaveBeenCalledWith('mockGeneSymbol');
    expect(getGeneScoresSpy.mock.calls).toEqual([// eslint-disable-line
      ['fakeScore1'],
      ['fakeScore2']
    ]);
    expect(component['genomicScoresGeneScores']).toStrictEqual([
      {category: 'fakeGenomicScore1', scores: 'fakeScore'},
      {category: 'fakeGenomicScore2', scores: 'fakeScore' }
    ] as any);

    geneMock = of({
      genomicScores: mockGenomicScores,
      geneSets: ['test1', 'test2', 'test3']
    } as any);
    component.isGeneInSFARI = false;
    getGeneSpy.mockReturnValue(geneMock);
    component.ngOnInit();
    expect(component['gene$']).toStrictEqual(geneMock);
    expect(component.isGeneInSFARI).toBeFalsy();

    getGeneSpy.mockReturnValueOnce(throwError(() => {
      new Error('FAIL');
    }));

    component.ngOnInit();
    expect(component.errorModal).toBe(true);
  });

  it('should get autism score gene score', () => {
    const mocksScores = [
      {category: 'autismScore', scores: [{score: 'score1'}, {score: 'score2'}]},
      {category: 'protectionScore', scores: [{score: 'score3'}, {score: 'score4'}]},
    ];
    component['genomicScoresGeneScores'] = mocksScores as any;
    expect(component.getGeneScoreByKey('autismScore', 'score1')).toStrictEqual({score: 'score1'} as any);
    expect(component.getGeneScoreByKey('autismScore', 'score2')).toStrictEqual({score: 'score2'}as any);
    expect(component.getGeneScoreByKey('protectionScore', 'score3')).toStrictEqual({score: 'score3'} as any);
    expect(component.getGeneScoreByKey('protectionScore', 'score4')).toStrictEqual({score: 'score4'} as any);
  });

  it('should get gene dataset value', () => {
    const mockGene = {
      studies: [
        {
          id: 'studyId1',
          personSets: [
            {
              id: 'personSetId1',
              effectTypes: [
                {
                  id: 'effectTypeId1'
                },
                {
                  id: 'effectTypeId2'
                }
              ]
            },
            {
              id: 'personSetId2',
              effectTypes: [
                {
                  id: 'effectTypeId3'
                },
                {
                  id: 'effectTypeId4'
                }
              ]
            }
          ]
        },
        {
          id: 'studyId2',
          personSets: [
            {
              id: 'personSetId3',
              effectTypes: [
                {
                  id: 'effectTypeId5'
                },
                {
                  id: 'effectTypeId6'
                }
              ]
            },
            {
              id: 'personSetId4',
              effectTypes: [
                {
                  id: 'effectTypeId7'
                },
                {
                  id: 'effectTypeId8'
                }
              ]
            }
          ]
        }
      ]
    };
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId1', 'effectTypeId1'))
      .toStrictEqual({id: 'effectTypeId1'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId1', 'effectTypeId2'))
      .toStrictEqual({id: 'effectTypeId2'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId2', 'effectTypeId3'))
      .toStrictEqual({id: 'effectTypeId3'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId2', 'effectTypeId4'))
      .toStrictEqual({id: 'effectTypeId4'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId3', 'effectTypeId5'))
      .toStrictEqual({id: 'effectTypeId5'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId3', 'effectTypeId6'))
      .toStrictEqual({id: 'effectTypeId6'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId4', 'effectTypeId7'))
      .toStrictEqual({id: 'effectTypeId7'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId4', 'effectTypeId8'))
      .toStrictEqual({id: 'effectTypeId8'} as any);
  });

  it('should get single score value', () => {
    const mocksScores = [
      { id: 'autismScore', scores: [
        { id: 'score1', value: 43, format: 'format' },
        { id: 'score2', value: 12, format: 'format' },
      ] as GeneProfilesGenomicScoreWithValue[]},
      { id: 'protectionScore', scores: [
        { id: 'score3', value: 56, format: 'format' },
        { id: 'score4', value: 39, format: 'format' },
      ] as GeneProfilesGenomicScoreWithValue[]}
    ];
    expect(component.getSingleScoreValue(
      mocksScores as GeneProfilesGenomicScores[],
      'protectionScore',
      'score4'))
      .toBe(39);
  });

  it.skip('should save genotype browser filters state to state', () => {
    fixture.detectChanges();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const goToQuerySpy = jest.spyOn(GeneProfileSingleViewComponent, 'goToQuery');
    const saveQuerySpy = jest.spyOn(queryServiceMock, 'saveQuery');

    const personSet = {
      id: 'personSetId',
      displayName: 'person set',
      collectionId: 'collectionId',
      description: '',
      parentsCount: 2,
      childrenCount: 0,
      defaultVisible: true,
      shown: [],
      statistics: []
    } as GeneProfilesDatasetPersonSet;

    const statistic = {
      id: 'personSetId',
      displayName: 'person set',
      effects: ['intron'],
      category: 'rare',
      description: '',
      variantTypes: ['type1', 'type2'],
      scores: [
        // {
        //   max: null,
        //   min: 2,
        //   name: 'mpc'
        // }
      ],
      defaultVisible: true
    } as GeneProfilesDatasetStatistic;

    component.goToQuery('chd8', personSet, 'datasetId', statistic);

    expect(goToQuerySpy).toHaveBeenCalledWith(
      store,
      queryServiceMock,
      'chd8',
      personSet,
      'datasetId',
      statistic
    );

    expect(dispatchSpy.mock.calls).toStrictEqual([
      [setGenomicScores({genomicScores: [new GenomicScore('a', 0, 10)]})],
      [setEffectTypes({effectTypes: ['intron']})],
      [setVariantTypes({variantTypes: ['type1', 'type2']})],
      [setGeneSymbols({geneSymbols: ['chd8']})],
      [setPresentInChild({presentInChild: ['proband only', 'proband and sibling', 'sibling only']})],
      [setPresentInParent({presentInParent: {
        presentInParent: ['father only', 'mother only', 'mother and father'],
        rarity: {
          rarityType: 'rare',
          rarityIntervalStart: 0,
          rarityIntervalEnd: 1
        }
      }})],
      [setPedigreeSelector({
        pedigreeSelector: {
          id: personSet.collectionId,
          checkedValues: [personSet.id]
        }
      })],
      [setStudyTypes({studyTypes: ['we']})]
    ]);

    expect(saveQuerySpy).toHaveBeenCalledTimes(1);
  });

  it('should go back from error modal', () => {
    jest.clearAllMocks();
    const dispatchSpy = jest.spyOn(store, 'dispatch');
    const selectSpy = jest.spyOn(store, 'select').mockReturnValueOnce(of({openedTabs: ['tab1', 'tab2', 'tab3']}));
    const routerSpy = jest.spyOn(component['router'], 'navigate');

    component.errorModal = true;
    Object.defineProperty(component, 'geneSymbol', {value: 'tab2' });
    component.errorModalBack();

    expect(component.errorModal).toBe(false);
    expect(selectSpy).toHaveBeenCalledWith(selectGeneProfiles);
    expect(dispatchSpy).toHaveBeenCalledWith(setGeneProfilesOpenedTabs({ openedTabs: ['tab1', 'tab3'] }));
    expect(routerSpy).toHaveBeenCalledWith(['/gene-profiles']);
  });
});
