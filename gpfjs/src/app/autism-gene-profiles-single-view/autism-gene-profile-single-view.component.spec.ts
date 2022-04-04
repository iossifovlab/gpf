import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { GeneScoresService } from 'app/gene-scores/gene-scores.service';
import { UsersService } from 'app/users/users.service';
import { of } from 'rxjs';
import { AutismGeneProfileSingleViewComponent } from './autism-gene-profile-single-view.component';
import { QueryService } from 'app/query/query.service';

describe('AutismGeneProfileSingleViewComponent', () => {
  let component: AutismGeneProfileSingleViewComponent;
  let fixture: ComponentFixture<AutismGeneProfileSingleViewComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [AutismGeneProfileSingleViewComponent],
      providers: [ConfigService, GeneScoresService, DatasetsService, UsersService, QueryService],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfileSingleViewComponent);
    component = fixture.componentInstance;
    component.config = {geneSets: ['mockGeneSet']} as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    (component as any).geneSymbol = 'mockGeneSymbol';
    const getGeneSpy = jest.spyOn(component['autismGeneProfilesService'], 'getGene');
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
    expect(component['gene$']).toEqual(geneMock);
    expect(component.isGeneInSFARI).toBeTruthy();
    expect(getGeneSpy).toHaveBeenCalledWith('mockGeneSymbol');
    expect(getGeneScoresSpy.mock.calls).toEqual([
      ['fakeScore1'],
      ['fakeScore2']
    ]);
    expect(component['genomicScoresGeneScores']).toEqual([
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
    expect(component['gene$']).toEqual(geneMock);
    expect(component.isGeneInSFARI).toBeFalsy();
  });

  it('should get autism score gene Score', () => {
    const mocksScores = [
      {category: 'autismScore', scores: [{Score: 'Score1'}, {Score: 'Score2'}]},
      {category: 'protectionScore', scores: [{Score: 'Score3'}, {Score: 'Score4'}]},
    ];
    component['genomicScoresGeneScores'] = mocksScores as any;
    expect(component.getGeneScoreByKey('autismScore', 'Score1')).toEqual({Score: 'Score1'} as any);
    expect(component.getGeneScoreByKey('autismScore', 'Score2')).toEqual({Score: 'Score2'}as any);
    expect(component.getGeneScoreByKey('protectionScore', 'Score3')).toEqual({Score: 'Score3'} as any);
    expect(component.getGeneScoreByKey('protectionScore', 'Score4')).toEqual({Score: 'Score4'} as any);
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
      .toEqual({id: 'effectTypeId1'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId1', 'effectTypeId2'))
      .toEqual({id: 'effectTypeId2'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId2', 'effectTypeId3'))
      .toEqual({id: 'effectTypeId3'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId1', 'personSetId2', 'effectTypeId4'))
      .toEqual({id: 'effectTypeId4'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId3', 'effectTypeId5'))
      .toEqual({id: 'effectTypeId5'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId3', 'effectTypeId6'))
      .toEqual({id: 'effectTypeId6'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId4', 'effectTypeId7'))
      .toEqual({id: 'effectTypeId7'} as any);
    expect(component.getGeneDatasetValue(mockGene as any, 'studyId2', 'personSetId4', 'effectTypeId8'))
      .toEqual({id: 'effectTypeId8'} as any);
  });

  it('should get browser url', () => {
    component.config = undefined;
    let link = component.getGeneBrowserLink();
    expect(link).toEqual(undefined);

    component.config = {defaultDataset: 'fakeDataset'} as any;
    (component as any).geneSymbol = 'fakeGeneSymbol';

    link = component.getGeneBrowserLink();
    expect(link.substring(link.indexOf('/datasets'))).toEqual(
      '/datasets/fakeDataset/gene-browser/fakeGeneSymbol'
    );
  });
});
