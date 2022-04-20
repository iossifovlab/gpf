import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { GeneWeightsService } from 'app/gene-weights/gene-weights.service';
import { UsersService } from 'app/users/users.service';
import { of } from 'rxjs';
import { AutismGeneProfileSingleViewComponent } from './autism-gene-profile-single-view.component';
import { QueryService } from 'app/query/query.service';

describe('AutismGeneProfileSingleViewComponent', () => {
  let component: AutismGeneProfileSingleViewComponent;
  let fixture: ComponentFixture<AutismGeneProfileSingleViewComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfileSingleViewComponent ],
      providers: [ConfigService, GeneWeightsService, DatasetsService, UsersService, QueryService],
      imports: [HttpClientTestingModule, RouterTestingModule, NgxsModule.forRoot([], {developmentMode: true})]
    })
    .compileComponents();
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

    const getGeneWeightsSpy = jest.spyOn(component['geneWeightsService'], 'getGeneWeights');
    getGeneWeightsSpy.mockReturnValue(of('fakeWeight' as any));

    expect(component.isGeneInSFARI).toBeFalsy();
    component.ngOnInit();
    expect(component['gene$']).toEqual(geneMock);
    expect(component.isGeneInSFARI).toBeTruthy();
    expect(getGeneSpy).toHaveBeenCalledWith('mockGeneSymbol');
    expect(getGeneWeightsSpy.mock.calls).toEqual([
      ['fakeScore1'],
      ['fakeScore2']
    ]);
    expect(component['genomicScoresGeneWeights']).toEqual([
      {category: 'fakeGenomicScore1', scores: 'fakeWeight'},
      {category: 'fakeGenomicScore2', scores: 'fakeWeight' }
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

  it('should get autism score gene weight', () => {
    const mocksWeights = [
      {category: 'autismScore', scores: [{weight: 'weight1'}, {weight: 'weight2'}]},
      {category: 'protectionScore', scores: [{weight: 'weight3'}, {weight: 'weight4'}]},
    ];
    component['genomicScoresGeneWeights'] = mocksWeights as any;
    expect(component.getGeneWeightByKey('autismScore', 'weight1')).toEqual({weight: 'weight1'} as any);
    expect(component.getGeneWeightByKey('autismScore', 'weight2')).toEqual({weight: 'weight2'}as any);
    expect(component.getGeneWeightByKey('protectionScore', 'weight3')).toEqual({weight: 'weight3'} as any);
    expect(component.getGeneWeightByKey('protectionScore', 'weight4')).toEqual({weight: 'weight4'} as any);
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

  it('should get histogram options', () => {
    component['_histogramOptions'] = {option: 'fakeOption'} as any;
    expect(component.histogramOptions).toEqual({option: 'fakeOption'} as any);
  });

  it('should get browser url', () => {
    component.config = undefined;
    let link = component.getGeneBrowserLink()
    expect(link).toEqual(undefined);

    component.config = {defaultDataset: 'fakeDataset'} as any;
    (component as any).geneSymbol = 'fakeGeneSymbol';

    link = component.getGeneBrowserLink();
    expect(link.substring(link.indexOf('/datasets'))).toEqual(
      '/datasets/fakeDataset/gene-browser/fakeGeneSymbol'
    );
  });
});
