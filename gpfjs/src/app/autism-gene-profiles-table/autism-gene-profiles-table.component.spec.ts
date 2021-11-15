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
import { Ng2SearchPipeModule } from 'ng2-search-filter';
// eslint-disable-next-line no-restricted-imports
import { of } from 'rxjs';
import { AgpConfig } from './autism-gene-profile-table';

import { AutismGeneProfilesTableComponent } from './autism-gene-profiles-table.component';

const mockConfig = {
  defaultDataset: 'fakeDefaultDataset',
  geneSets: [{category: 'fakeGeneSets', sets: ['fakeGeneSet']}] as any,
  genomicScores: [{category: 'fakeGenomicScores', scores: ['fakeGenomicScore']}] as any,
  datasets: [{id: 'fakeDataset', personSets: [{id: 'fakePersonSets', statistics: ['fakeStatistic']}]}] as any
} as AgpConfig;

describe('AutismGeneProfilesTableComponent', () => {
  let component: AutismGeneProfilesTableComponent;
  let fixture: ComponentFixture<AutismGeneProfilesTableComponent>;

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
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should update genes on window scroll', () => {
    const scrollTopSpy = spyOnProperty(document.documentElement, 'scrollTop');
    const offsetHeightSpy = spyOnProperty(document.documentElement, 'offsetHeight');
    const scrollHeightSpy = spyOnProperty(document.documentElement, 'scrollHeight');
    const updateGenesSpy = spyOn(component, 'updateGenes');
    const updateModalBottom = spyOn(component, 'updateModalBottom').and.callFake(() => {component.modalBottom = 1});

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

    expect(updateModalBottom).toHaveBeenCalledTimes(3);
    expect(component.modalBottom).toBe(1);
  });

  it('should calculate modal bottom', () => {
    component.columnFilteringButtons = {
      first: undefined
    } as any;
    component.updateModalBottom();
    expect(component.modalBottom).toBe(0);

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
    component.updateModalBottom();
    expect(component.modalBottom).toBe(1);

    innerHeightSpy.and.returnValue(11);
    clientHeightSpy.and.returnValue(22);
    component.updateModalBottom();
    expect(component.modalBottom).toBe(-14);
  });

  it('should emit create tab event', () => {
    const expectedEmitValue = {geneSymbol: 'testGeneSymbol', navigateToTab: true};

    const emitSpy = spyOn(component.createTabEvent, 'emit').and.callFake(emitValue => {
      expect(emitValue).toEqual(expectedEmitValue);
    });

    component.emitCreateTabEvent({ctrlKey: false, type: 'click'} as MouseEvent, 'testGeneSymbol');
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
