import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { ConfigService } from 'app/config/config.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { QueryService } from 'app/query/query.service';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { UsersService } from 'app/users/users.service';
import { cloneDeep } from 'lodash';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';
import { AgpTableConfig } from './autism-gene-profile-table';

import { AutismGeneProfilesTableComponent } from './autism-gene-profiles-table.component';

const mockConfig = {
  defaultDataset: 'fakeDefaultDataset',
  geneSets: [{category: 'fakeGeneSets', sets: ['fakeGeneSet']}] as any,
  genomicScores: [{category: 'fakeGenomicScores', scores: ['fakeGenomicScore']}] as any,
  datasets: [{id: 'fakeDataset', personSets: [{id: 'fakePersonSets', statistics: ['fakeStatistic']}]}] as any
} as AgpTableConfig;

describe('AutismGeneProfilesTableComponent', () => {
  let component: AutismGeneProfilesTableComponent;
  let fixture: ComponentFixture<AutismGeneProfilesTableComponent>;
  let applyDataSpy: jasmine.Spy<any>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        AutismGeneProfilesTableComponent,
        MultipleSelectMenuComponent,
        SortingButtonsComponent
      ],
      providers: [ConfigService, QueryService, DatasetsService, UsersService],
      imports: [
        Ng2SearchPipeModule,
        HttpClientTestingModule,
        FormsModule,
        RouterTestingModule,
        NgxsModule.forRoot([])
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesTableComponent);
    component = fixture.componentInstance;
    component.config = mockConfig;
    applyDataSpy = spyOn(component as any, 'multipleSelectMenuApplyData');
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should update genes on window scroll', () => {
    const scrollTopSpy = spyOnProperty(document.documentElement, 'scrollTop');
    const offsetHeightSpy = spyOnProperty(document.documentElement, 'offsetHeight');
    const scrollHeightSpy = spyOnProperty(document.documentElement, 'scrollHeight');
    const updateGenesSpy = spyOn(component, 'updateGenes');
    const calculateModalBottomSpy = spyOn(component, 'calculateModalBottom').and.returnValue(1);

    component['loadMoreGenes'] = false;
    component.onWindowScroll();
    expect(updateGenesSpy).not.toHaveBeenCalled();

    component['loadMoreGenes'] = true;
    scrollTopSpy.and.returnValue(1000 - component['scrollLoadThreshold']);
    offsetHeightSpy.and.returnValue(199);
    scrollHeightSpy.and.returnValue(1200);
    component.onWindowScroll();
    expect(updateGenesSpy).not.toHaveBeenCalled();

    offsetHeightSpy.and.returnValue(200);
    component.onWindowScroll();
    expect(updateGenesSpy).toHaveBeenCalledTimes(1);

    expect(calculateModalBottomSpy).toHaveBeenCalledTimes(3);
    expect(component.modalBottom).toBe(1);
  });

  it('should update shown categories on config change', () => {
    component.shownGeneSetsCategories = undefined;
    component.shownGenomicScoresCategories = undefined;
    component.shownDatasets = undefined;

    const mergerArraysSpy = spyOn(component, 'mergeArrays').and.returnValue('fakeArray' as any);

    component.ngOnChanges();
    expect(component.shownGeneSetsCategories).toEqual('fakeArray' as any);
    expect(component.shownGenomicScoresCategories).toEqual('fakeArray' as any);
    expect(component.shownDatasets).toEqual('fakeArray' as any);
  });

  it('should get genes on initialization', () => {
    component.shownGeneSetsCategories = undefined;
    component.shownGenomicScoresCategories = undefined;
    component.shownDatasets = undefined;
    component['genes'] = ['mockGene1', 'mockGene2', 'mockGene3'] as any;
    spyOn(component['autismGeneProfilesService'], 'getGenes')
      .and.returnValue(of(['mockGene4', 'mockGene5', 'mockGene6'] as any));

    component.ngOnInit();

    expect(component.shownGeneSetsCategories).toEqual([{category: 'fakeGeneSets', sets: ['fakeGeneSet']} as any]);
    expect(component.shownGenomicScoresCategories).toEqual([{category: 'fakeGenomicScores', scores: ['fakeGenomicScore']} as any]);
    expect(component.shownDatasets).toEqual([{id: 'fakeDataset', personSets: [{id: 'fakePersonSets', statistics: ['fakeStatistic']}]} as any]);
    expect((component['genes'])).toEqual([
      'mockGene1', 'mockGene2', 'mockGene3', 'mockGene4', 'mockGene5', 'mockGene6'
    ] as any);
  });

  it('should calculate modal bottom', () => {
    component.columnFilteringButtons = {
      first: undefined
    } as any;
    expect(component.calculateModalBottom()).toBe(0);

    component.columnFilteringButtons = {
      first: {
        nativeElement: {
          getBoundingClientRect() { return {bottom: 10}; }
        }
      }
    } as any;

    const innerHeightSpy = spyOnProperty(window, 'innerHeight');
    const clientHeightSpy = spyOnProperty(document.documentElement, 'clientHeight')

    innerHeightSpy.and.returnValue(11);
    clientHeightSpy.and.returnValue(11);
    expect(component.calculateModalBottom()).toBe(1);

    innerHeightSpy.and.returnValue(11);
    clientHeightSpy.and.returnValue(22);
    expect(component.calculateModalBottom()).toBe(-14);
  });

  it('should handle multiple select apply event for gene sets', () => {
    applyDataSpy.and.callThrough();
    component.ngbDropdownMenu = [{dropdown: {close() {}}}] as any;
    const emitSpy = spyOn(component.configChange, 'emit');
    const geneSetsArray = [
      {category: 'fakeGeneSets1', sets: [{setId: 'fakeGeneSet11'}, {setId: 'fakeGeneSet12'}]},
      {category: 'fakeGeneSets2', sets: [{setId: 'fakeGeneSet21'}, {setId: 'fakeGeneSet22'}]}
    ];

    component.config = {
      defaultDataset: 'fakeDefaultDataset',
      geneSets: geneSetsArray as any,
      genomicScores: undefined,
      datasets: undefined
    } as AgpTableConfig;

    component['shownGeneSetsCategories'] = geneSetsArray as any;

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'gene_set_category:fakeGeneSets1',
      data: ['fakeGeneSet12']
    });
    expect(component['shownGeneSetsCategories']).toEqual([
      {category: 'fakeGeneSets1', sets: [{setId: 'fakeGeneSet12'}]} as any,
      {category: 'fakeGeneSets2', sets: [{setId: 'fakeGeneSet21'}, {setId: 'fakeGeneSet22'}]}
    ]);
    expect(emitSpy).not.toHaveBeenCalled();

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'gene_set_category:fakeGeneSets1',
      data: []
    });
    expect(component['shownGeneSetsCategories']).toEqual([
      {category: 'fakeGeneSets2', sets: [{setId: 'fakeGeneSet21'}, {setId: 'fakeGeneSet22'}]}  as any
    ]);
    expect(emitSpy).toHaveBeenCalledTimes(1);
    expect(emitSpy.calls.allArgs()[0][0].geneSets).toEqual([
      {
          category: 'fakeGeneSets2',
          sets: [
              { setId: 'fakeGeneSet21' },
              { setId: 'fakeGeneSet22' }
          ]
      } as any
    ]);
  });

  it('should handle multiple select apply event for genomic scores', () => {
    applyDataSpy.and.callThrough();
    component.ngbDropdownMenu = [{dropdown: {close() {}}}] as any;
    const emitSpy = spyOn(component.configChange, 'emit');

    const genomicScoresArray = [
      {category: 'fakeGenomicScores1', scores: [{scoreName: 'fakeGenomicScore11'}, {scoreName: 'fakeGenomicScore12'}]},
      {category: 'fakeGenomicScores2', scores: [{scoreName: 'fakeGenomicScore21'}, {scoreName: 'fakeGenomicScore22'}]}
    ];

    component.config = {
      defaultDataset: 'fakeDefaultDataset',
      geneSets: undefined,
      genomicScores: genomicScoresArray as any,
      datasets: undefined
    } as AgpTableConfig;

    component['shownGenomicScoresCategories'] = genomicScoresArray as any;

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'genomic_scores_category:fakeGenomicScores1',
      data: ['fakeGenomicScore12']
    });
    expect(component['shownGenomicScoresCategories']).toEqual([
      {category: 'fakeGenomicScores1', scores: [{scoreName: 'fakeGenomicScore12'}]} as any,
      {category: 'fakeGenomicScores2', scores: [{scoreName: 'fakeGenomicScore21'}, {scoreName: 'fakeGenomicScore22'}]} as any
    ]);
    expect(emitSpy).not.toHaveBeenCalled();

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'genomic_scores_category:fakeGenomicScores1',
      data: []
    });
    expect(component['shownGenomicScoresCategories']).toEqual([
      {category: 'fakeGenomicScores2', scores: [{scoreName: 'fakeGenomicScore21'}, {scoreName: 'fakeGenomicScore22'}]} as any
    ]);
    expect(emitSpy).toHaveBeenCalledTimes(1);

    expect(emitSpy.calls.allArgs()[0][0].genomicScores).toEqual([
      {
          category: 'fakeGenomicScores2',
          scores: [
              { scoreName: 'fakeGenomicScore21' },
              { scoreName: 'fakeGenomicScore22' }
          ]
      } as any
    ]);
  });

  it('should handle multiple select apply event for datasets', () => {
    applyDataSpy.and.callThrough();
    component.ngbDropdownMenu = [{dropdown: {close() {}}}] as any;
    const emitSpy = spyOn(component.configChange, 'emit');
    component.config = cloneDeep(mockConfig);

    const datasetArray = [
      { id: 'fakeDataset1',
        personSets: [
          { id: 'fakePersonSetId11',
            displayName: 'fakePersonSet11',
            statistics: [{displayName: 'fakeStatistic11'}, {displayName: 'fakeStatistic12'}]},
          { id: 'fakePersonSetId12',
            displayName: 'fakePersonSet12',
            statistics: [{displayName: 'fakeStatistic13'}, {displayName: 'fakeStatistic14'}]}
        ]
      },
      { id: 'fakeDataset2',
        personSets: [
          { id: 'fakePersonSetId21',
            displayName: 'fakePersonSet21',
            statistics: [{displayName: 'fakeStatistic21'}, {displayName: 'fakeStatistic22'}]},
          { id: 'fakePersonSetId22',
            displayName: 'fakePersonSet22',
            statistics: [{displayName: 'fakeStatistic23'}, {displayName: 'fakeStatistic24'}]}
        ]
      }
    ];

    component.config = {
      defaultDataset: 'fakeDefaultDataset',
      geneSets: undefined,
      genomicScores: undefined,
      datasets: datasetArray as any
    } as AgpTableConfig;

    component.shownDatasets = datasetArray as any;

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'dataset:fakeDataset1',
      data: ['fakePersonSet12']
    });
    expect(component.shownDatasets).toEqual([
      { id: 'fakeDataset1',
        personSets: [
          { id: 'fakePersonSetId12',
            displayName: 'fakePersonSet12',
            statistics: [{displayName: 'fakeStatistic13'}, {displayName: 'fakeStatistic14'}]}
        ]
      },
      { id: 'fakeDataset2',
        personSets: [
          { id: 'fakePersonSetId21',
            displayName: 'fakePersonSet21',
            statistics: [{displayName: 'fakeStatistic21'}, {displayName: 'fakeStatistic22'}]},
          { id: 'fakePersonSetId22',
            displayName: 'fakePersonSet22',
            statistics: [{displayName: 'fakeStatistic23'}, {displayName: 'fakeStatistic24'}]}
        ]
      }
    ] as any);
    expect(emitSpy).not.toHaveBeenCalled();

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'dataset:fakeDataset1:fakePersonSetId12',
      data: ['fakeStatistic13']
    });
    expect(component.shownDatasets).toEqual([
      { id: 'fakeDataset1',
        personSets: [
          { id: 'fakePersonSetId12',
            displayName: 'fakePersonSet12',
            statistics: [{displayName: 'fakeStatistic13'}]}
        ]
      },
      { id: 'fakeDataset2',
        personSets: [
          { id: 'fakePersonSetId21',
            displayName: 'fakePersonSet21',
            statistics: [{displayName: 'fakeStatistic21'}, {displayName: 'fakeStatistic22'}]},
          { id: 'fakePersonSetId22',
            displayName: 'fakePersonSet22',
            statistics: [{displayName: 'fakeStatistic23'}, {displayName: 'fakeStatistic24'}]}
        ]
      }
    ] as any);
    expect(emitSpy).not.toHaveBeenCalled();

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'dataset:fakeDataset1:fakePersonSetId12',
      data: []
    });
    expect(component.shownDatasets).toEqual([
      { id: 'fakeDataset2',
        personSets: [
          { id: 'fakePersonSetId21',
            displayName: 'fakePersonSet21',
            statistics: [{displayName: 'fakeStatistic21'}, {displayName: 'fakeStatistic22'}]},
          { id: 'fakePersonSetId22',
            displayName: 'fakePersonSet22',
            statistics: [{displayName: 'fakeStatistic23'}, {displayName: 'fakeStatistic24'}]}
        ]
      }
    ] as any);
    expect(emitSpy).toHaveBeenCalledTimes(1);

    component.handleMultipleSelectMenuApplyEvent({
      menuId: 'dataset:fakeDataset2',
      data: []
    });
    expect(component.shownDatasets).toEqual([] as any);
    expect(emitSpy).toHaveBeenCalledTimes(2);

    expect(emitSpy.calls.allArgs()[0][0].datasets).toEqual([]);
    expect(emitSpy.calls.allArgs()[1][0].datasets).toEqual([]);
  });

  it('should emit create tab event', () => {
    const expectedEmitValue = {geneSymbol: 'testGeneSymbol', navigateToTab: true};

    const emitSpy = spyOn(component.createTabEvent, 'emit').and.callFake(emitValue => {
      expect(emitValue).toEqual(expectedEmitValue);
    });

    component.emitCreateTabEvent({ctrlKey: false, type: 'click'}, 'testGeneSymbol');
    expect(emitSpy).toHaveBeenCalled();
  });

  it('should update genes', () => {
    component['loadMoreGenes'] = true;
    component['genes'] = ['mockGene1', 'mockGene2', 'mockGene3'] as any;
    const getGenesSpy = spyOn(component['autismGeneProfilesService'], 'getGenes');

    getGenesSpy.and.returnValue(of(['mockGene4', 'mockGene5', 'mockGene6'] as any));
    component.updateGenes();
    expect(getGenesSpy).toHaveBeenCalledTimes(1);
    expect((component['genes'])).toEqual([
      'mockGene1', 'mockGene2', 'mockGene3', 'mockGene4', 'mockGene5', 'mockGene6'
    ] as any);
    expect(component['loadMoreGenes']).toBe(true);


    getGenesSpy.and.returnValue(of([] as any));
    component.updateGenes();
    expect(getGenesSpy).toHaveBeenCalledTimes(2);
    expect((component['genes'])).toEqual([
      'mockGene1', 'mockGene2', 'mockGene3', 'mockGene4', 'mockGene5', 'mockGene6'
    ] as any);
    expect(component['loadMoreGenes']).toBe(false);
  });

  it('should search for genes', () => {
    const updateGenesSpy = spyOn(component, 'updateGenes');
    expect(component.geneInput).toEqual(undefined);
    component.search('mockSearchString');
    expect(component.geneInput).toEqual('mockSearchString');
    expect(updateGenesSpy).toHaveBeenCalledTimes(1);
  });

  it('should sort with given parameters', () => {
    const updateGenesSpy = spyOn(component, 'updateGenes');

    component.sort('mockSortBy');
    expect(component.sortBy).toEqual('mockSortBy');
    expect(component.orderBy).toEqual(undefined);
    expect(updateGenesSpy).toHaveBeenCalledTimes(1);

    component.sort('mockSortBy', 'mockOrderBy');
    expect(component.sortBy).toEqual('mockSortBy');
    expect(component.orderBy).toEqual('mockOrderBy');
    expect(updateGenesSpy).toHaveBeenCalledTimes(2);
  });

  it('should send keystrokes', () => {
    const searchKeystrokesNextSpy = spyOn(component.searchKeystrokes$, 'next');
    component.sendKeystrokes('mockValue');
    expect(searchKeystrokesNextSpy).toHaveBeenCalledWith('mockValue');
  });
});
