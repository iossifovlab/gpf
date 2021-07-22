import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { Ng2SearchPipeModule } from 'ng2-search-filter';

import { MultipleSelectMenuComponent } from './multiple-select-menu.component';

const mockAllItems = [
  'item1',
  'item2',
  'item3',
  'item4',
  'item5'
];

const mockSelectedItems = [
  'item1',
  'item2',
];

describe('MultipleSelectMenuComponent', () => {
  let component: MultipleSelectMenuComponent;
  let fixture: ComponentFixture<MultipleSelectMenuComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [MultipleSelectMenuComponent],
      imports: [Ng2SearchPipeModule, FormsModule]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MultipleSelectMenuComponent);
    component = fixture.componentInstance;
    component.allItems = mockAllItems;
    component.selectedItems = mockSelectedItems;

    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should focus search on changes', () => {
    const focusSearchInputSpy = spyOn(component, 'focusSearchInput');
    component.focusInput = false;

    component.ngOnChanges();
    expect(focusSearchInputSpy).not.toHaveBeenCalled();

    component.focusInput = true;
    component.ngOnChanges();
    expect(focusSearchInputSpy).toHaveBeenCalledTimes(1);
  });

  it('should initialize', () => {
    component['checkboxDataArray'] = undefined;
    component['checkUncheckAllButtonName'] = 'Uncheck all';

    const areAllUncheckedSpy = spyOn(component, 'areAllUnchecked');
    areAllUncheckedSpy.and.returnValue(false);

    component.ngOnInit();
    expect(component['checkboxDataArray']).toEqual([
      {id: 'item1', isChecked: true},
      {id: 'item2', isChecked: true},
      {id: 'item3', isChecked: false},
      {id: 'item4', isChecked: false},
      {id: 'item5', isChecked: false}
    ]);
    expect(component['checkUncheckAllButtonName']).toEqual('Uncheck all');

    areAllUncheckedSpy.and.returnValue(true);

    component.ngOnInit();
    expect(component['checkUncheckAllButtonName']).toEqual('Check all');
  });

  it('should check if all are unchecked', () => {
    component.selectedItems = [];
    component.ngOnInit();
    expect(component.areAllUnchecked(component['checkboxDataArray'])).toBeTrue();

    component.selectedItems = [
      'item1'
    ];
    component.ngOnInit();
    expect(component.areAllUnchecked(component['checkboxDataArray'])).toBeFalse();

    component.selectedItems = [
      'item1',
      'item2'
    ];
    component.ngOnInit();
    expect(component.areAllUnchecked(component['checkboxDataArray'])).toBeFalse();
  });

  it('should toggle checking all', () => {
    component['checkUncheckAllButtonName'] = 'Uncheck all';
    component['checkboxDataArray'] = [
      {id: 'item1', isChecked: true},
      {id: 'item2', isChecked: true},
      {id: 'item3', isChecked: false},
      {id: 'item4', isChecked: true},
      {id: 'item5', isChecked: false}
    ];
    component.toggleCheckingAll();
    component['checkboxDataArray'].forEach(item => expect(item.isChecked).toBeFalse());
    expect(component['checkUncheckAllButtonName']).toEqual('Check all');

    component['checkboxDataArray'] = [
      {id: 'item1', isChecked: false},
      {id: 'item2', isChecked: true},
      {id: 'item3', isChecked: false},
      {id: 'item4', isChecked: true},
      {id: 'item5', isChecked: false}
    ];
    component.toggleCheckingAll();
    component['checkboxDataArray'].forEach(item => expect(item.isChecked).toBeTrue());
    expect(component['checkUncheckAllButtonName']).toEqual('Uncheck all');
  });

  it('should check if selection is valid', () => {
    component['checkboxDataArray'] = [
      {id: 'item1', isChecked: true},
      {id: 'item2', isChecked: true},
      {id: 'item3', isChecked: false},
      {id: 'item4', isChecked: true},
      {id: 'item5', isChecked: false}
    ];
    (component as any).minSelectCount = 3;
    expect(component.isSelectionValid()).toBeTrue();
    (component as any).minSelectCount = 4;
    expect(component.isSelectionValid()).toBeFalse();
  });

  it('should emit on apply event', () => {
    component.menuId = 'mockId';
    component['checkboxDataArray'] = [
      {id: 'item1', isChecked: true},
      {id: 'item2', isChecked: true},
      {id: 'item3', isChecked: false},
      {id: 'item4', isChecked: true},
      {id: 'item5', isChecked: false}
    ];
    const emitSpy = spyOn(component.applyEvent, 'emit');

    component.apply();
    expect(emitSpy).toHaveBeenCalledWith({
      menuId: 'mockId',
      data: ['item1', 'item2', 'item4']
    });
  });
});
