import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ConfigService } from 'app/config/config.service';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { Ng2SearchPipeModule } from 'ng2-search-filter';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';
import { AutismGeneToolConfig } from './autism-gene-profile-table';

import { AutismGeneProfilesTableComponent } from './autism-gene-profiles-table.component';

describe('AutismGeneProfilesTableComponent', () => {
  let component: AutismGeneProfilesTableComponent;
  let fixture: ComponentFixture<AutismGeneProfilesTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesTableComponent, MultipleSelectMenuComponent, SortingButtonsComponent],
      providers: [ConfigService],
      imports: [Ng2SearchPipeModule, HttpClientTestingModule, FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesTableComponent);
    component = fixture.componentInstance;
    component.config = new AutismGeneToolConfig(
      ['fakeAutismScores'],
      undefined,
      ['fakeGeneList'],
      ['fakeProtectionScores'],
      'fakeDefaultDataset'
    );
    fixture.detectChanges();
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

  it('should get genes on initialization', () => {
    component['genes'] = ['mockGene1', 'mockGene2', 'mockGene3'] as any;
    const getGenesSpy = spyOn(component['autismGeneProfilesService'], 'getGenes')
      .and.returnValue(of(['mockGene4', 'mockGene5', 'mockGene6'] as any));

    component.ngOnInit();
    expect(component['shownGeneSets']).toEqual(['fakeGeneList']);
    expect(component['shownAutismScores']).toEqual(['fakeAutismScores']);
    expect(component['shownProtectionScores']).toEqual(['fakeProtectionScores']);
    expect(getGenesSpy).toHaveBeenCalledTimes(1);
    expect((component['genes'])).toEqual([
      'mockGene1', 'mockGene2', 'mockGene3', 'mockGene4', 'mockGene5', 'mockGene6'
    ]);
  });

  it('should focus on gene search after view initialization', () => {
    const focuseGeneSearchSpy = spyOn(component, 'focusGeneSearch');
    expect(focuseGeneSearchSpy).not.toHaveBeenCalled();
    component.ngAfterViewInit();
    expect(focuseGeneSearchSpy).toHaveBeenCalledTimes(1);
  });

  it('should calculate dataset colspan', () => {
    let mockDatasetConfig;

    mockDatasetConfig = {effects: [1, 2], personSets: [1, 2]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(4);

    mockDatasetConfig = {effects: [1, 2, 3], personSets: [1, 2]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(6);

    mockDatasetConfig = {effects: [1, 2, 3, 4], personSets: [1, 2, 3, 4, 6, 7]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(24);

    mockDatasetConfig = {effects: [1, 2, 3, 4, 5], personSets: [1, 2, 3, 4, 6, 7, 8]};
    expect(component.calculateDatasetColspan(mockDatasetConfig)).toBe(35);
  });

  it('should handle multiple select apply event', () => {
    const dropDownMenuSpies = [];
    component.ngbDropdownMenu = [
      {dropdown: {close() {}}},
      {dropdown: {close() {}}},
      {dropdown: {close() {}}}
    ] as any;
    component.ngbDropdownMenu.forEach(menu => dropDownMenuSpies.push(spyOn(menu.dropdown, 'close')));

    component.handleMultipleSelectMenuApplyEvent({id: 'geneSets', data: ['fakeGeneSetsNew']});
    expect(component['shownGeneSets']).toEqual(['fakeGeneSetsNew']);
    expect(component['shownAutismScores']).toEqual((['fakeAutismScores']));
    expect(component['shownProtectionScores']).toEqual(['fakeProtectionScores']);
    dropDownMenuSpies.forEach(spy => expect(spy).toHaveBeenCalledTimes(1));

    component.handleMultipleSelectMenuApplyEvent({id: 'autismScores', data: ['fakeAutismScoresNew']});
    expect(component['shownGeneSets']).toEqual(['fakeGeneSetsNew']);
    expect(component['shownAutismScores']).toEqual((['fakeAutismScoresNew']));
    expect(component['shownProtectionScores']).toEqual(['fakeProtectionScores']);
    dropDownMenuSpies.forEach(spy => expect(spy).toHaveBeenCalledTimes(2));

    component.handleMultipleSelectMenuApplyEvent({id: 'protectionScores', data: ['fakeProtectionScoresNew']});
    expect(component['shownGeneSets']).toEqual(['fakeGeneSetsNew']);
    expect(component['shownAutismScores']).toEqual((['fakeAutismScoresNew']));
    expect(component['shownProtectionScores']).toEqual(['fakeProtectionScoresNew']);
    dropDownMenuSpies.forEach(spy => expect(spy).toHaveBeenCalledTimes(3));
  });

  it('should emit create tab event', () => {
    const expectedEmitValue = {geneSymbol: 'testGeneSymbol', openTab: true};

    const emitSpy = spyOn(component.createTabEvent, 'emit').and.callFake(emitValue => {
      expect(emitValue).toEqual(expectedEmitValue);
    });

    component.emitCreateTabEvent('testGeneSymbol', true);
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
    ]);
    expect(component['loadMoreGenes']).toBe(true);


    getGenesSpy.and.returnValue(of([] as any));
    component.updateGenes();
    expect(getGenesSpy).toHaveBeenCalledTimes(2);
    expect((component['genes'])).toEqual([
      'mockGene1', 'mockGene2', 'mockGene3', 'mockGene4', 'mockGene5', 'mockGene6'
    ]);
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
