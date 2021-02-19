import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgbNavModule } from '@ng-bootstrap/ng-bootstrap';
import { AutismGeneProfilesComponent } from 'app/autism-gene-profiles/autism-gene-profiles.component';
import { ConfigService } from 'app/config/config.service';
import { time } from 'console';

import { AutismGeneProfilesBlockComponent } from './autism-gene-profiles-block.component';

describe('AutismGeneProfilesBlockComponent', () => {
  let component: AutismGeneProfilesBlockComponent;
  let fixture: ComponentFixture<AutismGeneProfilesBlockComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AutismGeneProfilesBlockComponent, AutismGeneProfilesComponent ],
      providers: [ConfigService],
      imports: [HttpClientTestingModule, NgbNavModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AutismGeneProfilesBlockComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // it('should get config on initialization', () => {
  //   spyOn(component['autismGeneProfilesService'], 'getConfig')
  //    .and.returnValue(Observable.of('fakeConfig' as any));

  //   expect(component['autismGeneProfilesConfig']).toEqual(undefined);
  //   component.ngOnInit();
  //   component['autismGeneProfilesService'].getConfig().take(1)
  //    .subscribe(v => console.log(v));
  //   expect(component['autismGeneProfilesConfig']).toEqual('fakeConfig');
  // });

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
    const openTabAtIndexSpy = spyOn(component, 'openTabAtIndex').and.callFake(arg => {
      expect(arg).toBe(54639824 - 1);
    });

    getActiveTabIndexSpy.and.returnValue(0);
    component.openPreviousTab();
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).not.toHaveBeenCalled();

    getActiveTabIndexSpy.and.returnValue(54639824);
    component.openPreviousTab();
    expect(openHomeTabSpy).toHaveBeenCalledTimes(1);
    expect(openTabAtIndexSpy).toHaveBeenCalledTimes(1);
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

  // it('should close active tab', () => {
  //   const mockSet = new Set();
  //   mockSet.add('id1');
  //   mockSet.add('id2');
  //   mockSet.add('id3');
  //   mockSet.add('id4');
  //   component['geneTabs'] = mockSet as any;

  //   const geneTabsDeleteSpy = spyOn(component['geneTabs'], 'delete').and.callFake(arg => {
  //     expect(arg).toEqual('mockId');
  //     return true;
  //   });
  //   const openHomeTabSpy = spyOn(component, 'openHomeTab');
  //   const openLastTabSpy = spyOn(component, 'openLastTab');
  //   const openTabAtIndexSpy = spyOn(component, 'openTabAtIndex').and.callFake(arg => {
  //     expect(arg).toBe(54639824 - 1);
  //   });

  //   component['nav'] = {activeId: 'autismGenesTool'} as any;
  //   component.closeActiveTab();
  //   expect(geneTabsDeleteSpy).not.toHaveBeenCalled();
  //   expect(openHomeTabSpy).not.toHaveBeenCalled();
  //   expect(openLastTabSpy).not.toHaveBeenCalled();
  //   expect(openTabAtIndexSpy).not.toHaveBeenCalled();
  // });

  // it('should open tab by key', () => {

  // });
});
