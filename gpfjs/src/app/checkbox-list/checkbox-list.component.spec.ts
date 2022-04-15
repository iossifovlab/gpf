import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { CheckboxListComponent, DisplayNamePipe } from './checkbox-list.component';

describe('CheckboxListComponent', () => {
  let component: CheckboxListComponent;
  let fixture: ComponentFixture<CheckboxListComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CheckboxListComponent, DisplayNamePipe ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CheckboxListComponent);
    component = fixture.componentInstance;
    component.items = new Set(['testItem1', 'testItem2']);

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize', () => {
    const selectAllSpy = jest.spyOn(component, 'selectAll');

    component.selectedItems = new Set();
    component.ngOnInit();
    expect(selectAllSpy).not.toHaveBeenCalled();

    component.selectedItems = undefined;
    component.ngOnInit();
    expect(selectAllSpy).toHaveBeenCalled();
  });

  it('should emit', () => {
    component.itemsUpdateEvent = {emit() {}} as any;
    const emitSpy = jest.spyOn(component.itemsUpdateEvent, 'emit');

    component.selectedItems = undefined;
    component.emit();
    component.selectedItems = new Set([...component.items]);
    component.emit();

    expect(emitSpy.mock.calls).toEqual([
      [undefined],
      [component.selectedItems]
    ]);
  });

  it('should select none', () => {
    const emitSpy = jest.spyOn(component, 'emit');
    component.selectedItems = new Set([...component.items]);

    component.selectNone();
    expect(component.selectedItems).toEqual(new Set([]));
    expect(emitSpy).toHaveBeenCalled();
  });

  it('should select all', () => {
    const emitSpy = jest.spyOn(component, 'emit');
    component.selectedItems = new Set([]);

    component.selectAll();
    expect(component.selectedItems).toEqual(new Set([...component.items]));
    expect(emitSpy).toHaveBeenCalled();
  });

  it('should toggle item', () => {
    const emitSpy = jest.spyOn(component, 'emit');

    component.toggleItem('testItem3');
    expect(component.selectedItems).toEqual(new Set(['testItem1', 'testItem2', 'testItem3']));
    expect(emitSpy).toHaveBeenCalledTimes(1);
    component.toggleItem('testItem2');
    expect(component.selectedItems).toEqual(new Set(['testItem1', 'testItem3']));
    expect(emitSpy).toHaveBeenCalledTimes(2);
  });
});
