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

const mockSelectedItems = new Set([
  'item1',
  'item2',
]);

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

  it('should initialize', () => {
    component['checkboxDataArray'] = undefined;
    component['checkUncheckAllButtonName'] = 'Uncheck all';

    component.ngOnInit();
    expect(component['selectedItems']).toEqual(new Set(['item1', 'item2']));
    expect(component['checkUncheckAllButtonName']).toEqual('Uncheck all');
  });

  it('should toggle checking all', () => {
    component['checkUncheckAllButtonName'] = 'Uncheck all';
    component['selectedItems'] = new Set(['item1', 'item2', 'item4']);
    component.toggleCheckingAll();
    expect(component['selectedItems'].size).toEqual(0);
    expect(component['checkUncheckAllButtonName']).toEqual('Check all');

    component['selectedItems'] = new Set(['item2', 'item4']);
    component.toggleCheckingAll();
    expect(component['selectedItems'].size).toEqual(5);
    expect(component['checkUncheckAllButtonName']).toEqual('Uncheck all');
  });

  it('should emit on apply event', () => {
    component.menuId = 'mockId';
    component['selectedItems'] = new Set(['item1', 'item2', 'item4']);
    const emitSpy = spyOn(component.applyEvent, 'emit');

    component.apply();
    expect(emitSpy).toHaveBeenCalledWith({
      menuId: 'mockId',
      order: ['item1', 'item2', 'item3', 'item4', 'item5'],
      selected: ['item1', 'item2', 'item4']
    });
  });
});
