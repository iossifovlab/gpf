import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { AutismGeneProfilesTableComponent } from 'app/autism-gene-profiles-table/autism-gene-profiles-table.component';
import { ConfigService } from 'app/config/config.service';
// tslint:disable-next-line:import-blacklist
import { of } from 'rxjs';

import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block.component';

describe('AutismGeneProfilesBlockComponent', () => {
  let component: AutismGeneProfilesBlockComponent;
  let fixture: ComponentFixture<AutismGeneProfilesBlockComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesBlockComponent, AutismGeneProfilesTableComponent ],
      providers: [ConfigService],
      imports: [HttpClientTestingModule, NgbNavModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    component.nav = {
      select(id: any) {},
      activeId: '',
    } as any;
  });

  it('should listen for key press events', () => {
    const closeActiveTabSpy = spyOn(component, 'closeActiveTab');
    const openTabByKeySpy = spyOn(component, 'openTabByKey');

    let mockEvent = {key: 'w', target: {localName: 'input'}};
    component.keyEvent(mockEvent as any);
    expect(closeActiveTabSpy).not.toHaveBeenCalled();
    expect(openTabByKeySpy).not.toHaveBeenCalled();

    mockEvent = {key: 'w', target: {localName: 'notInput'}};
    component.keyEvent(mockEvent as any);
    expect(closeActiveTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabByKeySpy).not.toHaveBeenCalled();

    const tabKeys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'p', 'n'];
    tabKeys.forEach(tabKey => {
      mockEvent = {key: tabKey, target: {localName: 'notInput'}};
      component.keyEvent(mockEvent as any);
      expect(closeActiveTabSpy).toHaveBeenCalledTimes(1);
      expect(openTabByKeySpy).toHaveBeenCalledWith(tabKey);
    });
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get config on initialization', () => {
    spyOn(component['autismGeneProfilesService'], 'getConfig')
     .and.returnValue(of('fakeConfig' as any));
    spyOn(component, 'getTableConfig')
     .and.returnValue('fakeTableConfig' as any);
    spyOn(component, 'getAllCategories')
     .and.returnValue('fakeCategories' as any);

    expect(component.autismGeneToolConfig).toEqual(undefined);
    expect(component.tableConfig).toEqual(undefined);
    expect(component.shownTableConfig).toEqual(undefined);
    expect(component.allColumns).toEqual(undefined);
    expect(component.shownColumns).toEqual(undefined);
    component.ngOnInit();
    expect(component.autismGeneToolConfig).toEqual('fakeConfig' as any);
    expect(component.tableConfig).toEqual('fakeTableConfig' as any);
    expect(component.shownTableConfig).toEqual('fakeTableConfig' as any);
    expect(component.allColumns).toEqual('fakeCategories' as any);
    expect(component.shownColumns).toEqual('fakeCategories' as any);
  });

  it('should create tab event handler', () => {
    const navSpy = spyOn(component['nav'], 'select').and.callFake(arg => {
      expect(arg).toEqual('secondFakeTabId');
    });
    const expectedSet = new Set();

    component.createTabEventHandler({geneSymbol: 'firstFakeTabId', openTab: false});
    expectedSet.add('firstFakeTabId');
    expect(component['geneTabs']).toEqual(expectedSet);
    expect(navSpy).not.toHaveBeenCalled();

    component.createTabEventHandler({geneSymbol: 'secondFakeTabId', openTab: true});
    expectedSet.add('secondFakeTabId');
    expect(component['geneTabs']).toEqual(expectedSet);
    expect(navSpy).toHaveBeenCalled();
  });

  it('should get active tab index', () => {
    const mockSet = new Set();
    mockSet.add('id1');
    mockSet.add('id2');
    mockSet.add('id3');
    mockSet.add('id4');
    component['geneTabs'] = mockSet as any;

    component['nav'] = {activeId: 'id1'} as any;
    expect(component.getActiveTabIndex()).toBe(0);

    component['nav'] = {activeId: 'id2'} as any;
    expect(component.getActiveTabIndex()).toBe(1);

    component['nav'] = {activeId: 'id3'} as any;
    expect(component.getActiveTabIndex()).toBe(2);

    component['nav'] = {activeId: 'id4'} as any;
    expect(component.getActiveTabIndex()).toBe(3);
  });

  it('should open home tab', () => {
    const navSelectSpy = spyOn(component['nav'], 'select').and.callFake(arg => {
      expect(arg).toEqual('autismGenesTool');
    });

    component.openHomeTab();
    expect(navSelectSpy).toHaveBeenCalledTimes(1);
  });

  it('should open previous tab', () => {
    const getActiveTabIndexSpy = spyOn(component, 'getActiveTabIndex');
    const openHomeTabSpy = spyOn(component, 'openHomeTab');
    const openTabAtIndexSpy = spyOn(component, 'openTabAtIndex').and.callThrough();

    getActiveTabIndexSpy.and.returnValue(0);
    component.openPreviousTab();
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();

    getActiveTabIndexSpy.and.returnValue(5);
    component.openPreviousTab();
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).toHaveBeenCalledWith(4);
    getActiveTabIndexSpy.and.returnValue(4);
    component.openPreviousTab();
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).toHaveBeenCalledWith(3);
    getActiveTabIndexSpy.and.returnValue(3);
    component.openPreviousTab();
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).toHaveBeenCalledWith(2);
  });

  it('should open next tab', () => {
    const mockSet = new Set();
    mockSet.add('id1');
    mockSet.add('id2');
    mockSet.add('id3');
    mockSet.add('id4');
    component['geneTabs'] = mockSet as any;

    const getActiveTabIndexSpy = spyOn(component, 'getActiveTabIndex');
    let index;

    const openTabAtIndexSpy = spyOn(component, 'openTabAtIndex').and.callFake(arg => {
      switch (index) {
        case 0: expect(arg).toBe(1); break;
        case 1: expect(arg).toBe(2); break;
        case 2: expect(arg).toBe(3); break;
      }
    });

    for (let i = 0; i < 4; i++) {
      index = i;
      getActiveTabIndexSpy.and.returnValue(index);
      component.openNextTab();
    }

    expect(openTabAtIndexSpy).toHaveBeenCalledTimes(3);
  });

  it('should open last tab', () => {
    const mockSet = new Set();
    mockSet.add('id1');
    mockSet.add('id2');
    mockSet.add('id3');
    mockSet.add('id4');
    component['geneTabs'] = mockSet as any;

    const navSpy = spyOn(component['nav'], 'select').and.callFake(arg => {
      expect(arg).toEqual('id4');
    });

    component.openLastTab();
    expect(navSpy).toHaveBeenCalledTimes(1);
  });

  it('should open tab at index', () => {
    const mockSet = new Set();
    mockSet.add('id1');
    mockSet.add('id2');
    mockSet.add('id3');
    mockSet.add('id4');
    component['geneTabs'] = mockSet as any;

    let index;
    const navSpy = spyOn(component['nav'], 'select').and.callFake(arg => {
      switch (index) {
        case 0: expect(arg).toEqual('id1'); break;
        case 1: expect(arg).toEqual('id2'); break;
        case 2: expect(arg).toEqual('id3'); break;
        case 3: expect(arg).toEqual('id4'); break;
      }
    });

    for (let i = 0; i < 4; i++) {
      index = i;
      component.openTabAtIndex(index);
    }

    expect(navSpy).toHaveBeenCalledTimes(4);
  });

  it('should close tab', () => {
    const mockEvent = {preventDefault() { }, stopImmediatePropagation() { }};
    component['nav'] = {activeId: 'mockActiveId'} as any;
    const closeActiveTabSpy = spyOn(component, 'closeActiveTab');
    const geneTabsDeleteSpy = spyOn(component['geneTabs'], 'delete').and.callFake(arg => {
      expect(arg).toEqual('mockId');
      return true;
    });
    const preventDefaultSpy = spyOn(mockEvent, 'preventDefault');
    const stopImmediatePropagationSpy = spyOn(mockEvent, 'stopImmediatePropagation');

    component.closeTab(mockEvent as any, 'autismGenesTool');
    expect(closeActiveTabSpy).not.toHaveBeenCalled();
    expect(geneTabsDeleteSpy).not.toHaveBeenCalled();
    expect(preventDefaultSpy).not.toHaveBeenCalled();
    expect(stopImmediatePropagationSpy).not.toHaveBeenCalled();

    component.closeTab(mockEvent as any, 'mockActiveId');
    expect(closeActiveTabSpy).toHaveBeenCalledTimes(1);
    expect(geneTabsDeleteSpy).not.toHaveBeenCalled();
    expect(preventDefaultSpy).toHaveBeenCalledTimes(1);
    expect(stopImmediatePropagationSpy).toHaveBeenCalledTimes(1);

    component.closeTab(mockEvent as any, 'mockId');
    expect(closeActiveTabSpy).toHaveBeenCalledTimes(1);
    expect(geneTabsDeleteSpy).toHaveBeenCalledTimes(1);
    expect(preventDefaultSpy).toHaveBeenCalledTimes(2);
    expect(stopImmediatePropagationSpy).toHaveBeenCalledTimes(2);
  });

  it('should close active tab', () => {
    const openHomeTabSpy = spyOn(component, 'openHomeTab');
    const openLastTabSpy = spyOn(component, 'openLastTab');
    const openTabAtIndexSpy = spyOn(component, 'openTabAtIndex');

    component['nav'] = {activeId: 'autismGenesTool'} as any;
    component.closeActiveTab();
    expect(openHomeTabSpy).not.toHaveBeenCalled();
    expect(openLastTabSpy).not.toHaveBeenCalled();
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();

    component['geneTabs'].add('id1');
    component['nav'] = {activeId: 'id1'} as any;
    component.closeActiveTab();
    expect(component['geneTabs'].has('id1')).toBe(false);
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openLastTabSpy).not.toHaveBeenCalled();
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();

    component['geneTabs'].add('id1');
    component['geneTabs'].add('id2');
    component['nav'] = {activeId: 'id2'} as any;

    component.closeActiveTab();
    expect(component['geneTabs'].has('id2')).toBe(false);
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openLastTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();

    component['geneTabs'].add('id2');

    component['nav'] = {activeId: 'id1'} as any;
    component.closeActiveTab();
    expect(component['geneTabs'].has('id1')).toBe(false);
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openLastTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).toHaveBeenCalledWith(0);
  });

  it('should open tab by key', () => {
    const openLastTabSpy = spyOn(component, 'openLastTab');
    const openHomeTabSpy = spyOn(component, 'openHomeTab');
    const openTabAtIndexSpy = spyOn(component, 'openTabAtIndex');
    const openPreviousTabSpy = spyOn(component, 'openPreviousTab');
    const openNextTabSpy = spyOn(component, 'openNextTab');

    component.openTabByKey('n');
    expect(openLastTabSpy).not.toHaveBeenCalled();
    expect(openHomeTabSpy).not.toHaveBeenCalled();
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();
    expect(openPreviousTabSpy).not.toHaveBeenCalled();
    expect(openNextTabSpy).not.toHaveBeenCalled();

    component['geneTabs'].add('id1');
    component['geneTabs'].add('id2');
    component['geneTabs'].add('id3');
    component['geneTabs'].add('id4');

    component.openTabByKey('0');
    expect(openLastTabSpy).toHaveBeenCalledTimes(1);

    expect(openHomeTabSpy).not.toHaveBeenCalled();
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();
    expect(openPreviousTabSpy).not.toHaveBeenCalled();
    expect(openNextTabSpy).not.toHaveBeenCalled();

    component.openTabByKey('1');
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);

    expect(openLastTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();
    expect(openPreviousTabSpy).not.toHaveBeenCalled();
    expect(openNextTabSpy).not.toHaveBeenCalled();

    component.openTabByKey('2');
    expect(openTabAtIndexSpy).toHaveBeenCalledWith(0);
    component.openTabByKey('3');
    expect(openTabAtIndexSpy).toHaveBeenCalledWith(1);

    expect(openLastTabSpy).toHaveBeenCalledTimes(1);
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openPreviousTabSpy).not.toHaveBeenCalled();
    expect(openNextTabSpy).not.toHaveBeenCalled();

    component.openTabByKey('p');
    expect(openPreviousTabSpy).toHaveBeenCalledTimes(1);
    component.openTabByKey('n');
    expect(openNextTabSpy).toHaveBeenCalledTimes(1);

    expect(openLastTabSpy).toHaveBeenCalledTimes(1);
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).toHaveBeenCalledTimes(2);
  });

  it('should get all categories', () => {
    const mockConfig = {
      geneSets: [
        { displayName: 'geneSetCategory1' },
        { displayName: 'geneSetCategory2' },
        { displayName: 'geneSetCategory3' },
      ],
      genomicScores: [
        { displayName: 'genomicScoreCategory1' },
        { displayName: 'genomicScoreCategory2' },
        { displayName: 'genomicScoreCategory3' },
      ],
      datasets: [
        { displayName: 'dataset1' },
        { displayName: 'dataset2' },
        { displayName: 'dataset3' },
      ],
    };
    expect(component.getAllCategories(mockConfig as any)).toEqual([
      'geneSetCategory1',
      'geneSetCategory2',
      'geneSetCategory3',
      'genomicScoreCategory1',
      'genomicScoreCategory2',
      'genomicScoreCategory3',
      'dataset1',
      'dataset2',
      'dataset3'
    ]);
  });

  it('should handle multiple select menu apply event', () => {
    component.ngbDropdownMenu = {dropdown: {close() {}}} as any;
    expect(component.shownTableConfig).toEqual(undefined);
    expect(component.shownColumns).toEqual(undefined);
    component.shownTableConfig = {
      geneSets: [],
      genomicScores: [],
      datasets: [],
    } as any;
    component.tableConfig = {
      geneSets: [
        { displayName: 'geneSetCategory1' },
        { displayName: 'geneSetCategory2' },
        { displayName: 'geneSetCategory3' },
      ],
      genomicScores: [
        { displayName: 'genomicScoreCategory1' },
        { displayName: 'genomicScoreCategory2' },
        { displayName: 'genomicScoreCategory3' },
      ],
      datasets: [
        { displayName: 'dataset1' },
        { displayName: 'dataset2' },
        { displayName: 'dataset3' },
      ],
    } as any;

    component.handleMultipleSelectMenuApplyEvent({
      data: [
        'geneSetCategory1',
        'genomicScoreCategory2',
        'dataset3'
      ]
    });
    expect(component.shownColumns).toEqual([
      'geneSetCategory1',
      'genomicScoreCategory2',
      'dataset3'
    ]);
    expect(component.shownTableConfig).toEqual({
      geneSets: [
        { displayName: 'geneSetCategory1' },
      ],
      genomicScores: [
        { displayName: 'genomicScoreCategory2' },
      ],
      datasets: [
        { displayName: 'dataset3' },
      ],
    } as any);

    component.handleMultipleSelectMenuApplyEvent({
      data: [
        'geneSetCategory1',
        'geneSetCategory3',
        'genomicScoreCategory1',
        'genomicScoreCategory2',
        'dataset2',
        'dataset3'
      ]
    });
    expect(component.shownColumns).toEqual([
      'geneSetCategory1',
      'geneSetCategory3',
      'genomicScoreCategory1',
      'genomicScoreCategory2',
      'dataset2',
      'dataset3'
    ]);
    expect(component.shownTableConfig).toEqual({
      geneSets: [
        { displayName: 'geneSetCategory1' },
        { displayName: 'geneSetCategory3' },
      ],
      genomicScores: [
        { displayName: 'genomicScoreCategory1' },
        { displayName: 'genomicScoreCategory2' },
      ],
      datasets: [
        { displayName: 'dataset2' },
        { displayName: 'dataset3' },
      ],
    } as any);

  });
});
