import { NO_ERRORS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ALL_STATES } from './present-in-child';

import { PresentInChildComponent } from './present-in-child.component';

describe('PresentInChildComponent', () => {
  let component: PresentInChildComponent;
  let fixture: ComponentFixture<PresentInChildComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PresentInChildComponent ],
      schemas: [NO_ERRORS_SCHEMA]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PresentInChildComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get state on init', () => {
    const getStateSpy = spyOn(component['stateRestoreService'], 'getState');

    const expectedDefaultSet = new Set();
    expectedDefaultSet.add('proband only').add('proband and sibling');
    getStateSpy.and.returnValue(of());
    component.ngOnInit();
    expect(component.presentInChild.selected).toEqual(expectedDefaultSet);

    const expectedMockSet = new Set();
    expectedMockSet.add('Mock data');
    getStateSpy.and.returnValue(of({presentInChild: expectedMockSet}));
    component.ngOnInit();
    expect(component.presentInChild.selected).toEqual(expectedMockSet);
  });

  it('should select all', () => {
    component.presentInChild.selected = undefined;
    component.selectAll();
    expect(component.presentInChild.selected).toEqual(new Set(ALL_STATES));
  });

  it('should select none', () => {
    component.presentInChild.selected = undefined;
    component.selectNone();
    expect(component.presentInChild.selected).toEqual(new Set());
  });

  it('should check value', () => {
    component.presentInChild.selected = new Set();
    component.presentInChildCheckValue('mockKey1', true);
    expect(component.presentInChild.selected).toEqual(new Set(['mockKey1']));
    component.presentInChildCheckValue('mockKey2', true);
    expect(component.presentInChild.selected).toEqual(new Set(['mockKey1', 'mockKey2']));
    component.presentInChildCheckValue('mockKey1', false);
    expect(component.presentInChild.selected).toEqual(new Set(['mockKey2']));
    component.presentInChildCheckValue('mockKey2', false);
    expect(component.presentInChild.selected).toEqual(new Set());
  });

  it('should get state', () => {
    component.presentInChild.selected = new Set();
    component.presentInChildCheckValue('mockKey1', true);
    component.presentInChildCheckValue('mockKey2', true);
    component.presentInChildCheckValue('mockKey3', true);

    component.getState().subscribe(state =>
      expect(state).toEqual({presentInChild: ['mockKey1', 'mockKey2', 'mockKey3']})
    );
  });
});
