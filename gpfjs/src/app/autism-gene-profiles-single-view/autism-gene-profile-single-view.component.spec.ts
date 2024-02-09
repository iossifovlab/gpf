import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { GeneScoresService } from 'app/gene-scores/gene-scores.service';
import { UsersService } from 'app/users/users.service';
import { of } from 'rxjs';
import { GeneProfileSingleViewComponent } from './autism-gene-profile-single-view.component';
import { QueryService } from 'app/query/query.service';
import { APP_BASE_HREF } from '@angular/common';

describe('GeneProfileSingleViewComponent', () => {
  let component: GeneProfileSingleViewComponent;
  let fixture: ComponentFixture<GeneProfileSingleViewComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [GeneProfileSingleViewComponent],
      providers: [
        ConfigService, GeneScoresService, DatasetsService,
        UsersService, QueryService, { provide: APP_BASE_HREF, useValue: '' }
      ],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();

    fixture = TestBed.createComponent(GeneProfileSingleViewComponent);
    component = fixture.componentInstance;
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

  it('should get browser url', () => {
    component.config = undefined;
    let link = component.getGeneBrowserLink();
    expect(link).toBeUndefined();

    component.config = {defaultDataset: 'fakeDataset'} as any;
    (component as any).geneSymbol = 'fakeGeneSymbol';

    link = component.getGeneBrowserLink();
    expect(link.substring(link.indexOf('/datasets'))).toBe(
      '/datasets/fakeDataset/gene-browser/fakeGeneSymbol'
    );
  });
});
