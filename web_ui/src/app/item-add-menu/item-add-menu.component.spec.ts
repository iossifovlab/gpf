import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { Observable, of } from 'rxjs';
import { Item } from './item-add-menu';

import { ItemAddMenuComponent } from './item-add-menu.component';
import { FormsModule } from '@angular/forms';

describe('ItemAddMenuComponent', () => {
  let component: ItemAddMenuComponent;
  let fixture: ComponentFixture<ItemAddMenuComponent>;

  const item1 = new Item('1', 'item1');
  const item2 = new Item('2', 'item2');
  const item3 = new Item('3', 'item3');
  const item4 = new Item('4', 'item4');
  const item5 = new Item('5', 'item5');
  const item6 = new Item('6', 'item6');

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [
        ItemAddMenuComponent,
      ],
      imports: [
        FormsModule
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ItemAddMenuComponent);
    component = fixture.componentInstance;

    component.getItems = (page: number, searchText: string): Observable<Item[]> => {
      if (page === 1) {
        return of([item1, item2, item3]);
      } else if (page === 2) {
        return of([item4, item5, item6]);
      }
      return of([] as Item[]);
    };
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should add item', () => {
    component.items = [item1, item2, item3];
    const emitSpy = jest.spyOn(component.addedItem, 'emit');

    component.addItem(item2);
    expect(component.items).toStrictEqual([item1, item3]);
    expect(emitSpy).toHaveBeenLastCalledWith(item2);

    component.addItem(item1);
    expect(component.items).toStrictEqual([item3]);
    expect(emitSpy).toHaveBeenLastCalledWith(item1);
  });

  it('should search', () => {
    const getItemsSpy = jest.spyOn(component, 'getItems');
    fixture.debugElement.query(By.css('.add-button')).triggerEventHandler('click', {});

    expect(getItemsSpy).toHaveBeenCalledTimes(1);
    expect(getItemsSpy).toHaveBeenCalledWith(1, '');

    component.search('item3');
    expect(getItemsSpy).toHaveBeenCalledTimes(2);
    expect(getItemsSpy).toHaveBeenCalledWith(1, 'item3');
    expect(component.items).toStrictEqual([item1, item2, item3]);

    component.search('item1');
    expect(getItemsSpy).toHaveBeenCalledTimes(3);
    expect(getItemsSpy).toHaveBeenCalledWith(1, 'item1');
    expect(component.items).toStrictEqual([item1, item2, item3]);
  });

  it('should request item list update when list is scrolled', () => {
    const searchSpy = jest.spyOn(component, 'search');
    const getItemsSpy = jest.spyOn(component, 'getItems');

    fixture.debugElement.query(By.css('.add-button')).triggerEventHandler('click', {});
    fixture.detectChanges();
    const tableContainer = fixture.debugElement.query(By.css('.table-container'));

    expect(searchSpy).toHaveBeenCalledTimes(1);
    expect(getItemsSpy).toHaveBeenCalledWith(1, '');
    expect(component.items).toStrictEqual([item1, item2, item3]);

    Object.defineProperty(tableContainer.nativeElement as HTMLElement, 'offsetHeight', {value: 1000});
    Object.defineProperty(tableContainer.nativeElement as HTMLElement, 'scrollTop', {value: 1000});
    Object.defineProperty(tableContainer.nativeElement as HTMLElement, 'scrollHeight', {value: 2000});

    tableContainer.triggerEventHandler('scroll', tableContainer);
    expect(getItemsSpy).toHaveBeenCalledWith(2, '');
    expect(component.items).toStrictEqual([item1, item2, item3, item4, item5, item6]);
  });

  it('should close menu when clicking outside', () => {
    // Simulate opening the menu
    fixture.debugElement.query(By.css('.add-button')).triggerEventHandler('click', {});

    // Simulate click inside the menu
    component.clickInside();
    component.allClicks();

    expect(component.showMenu).toBe(true);

    // Simulate click outside the menu
    component.allClicks();

    expect(component.showMenu).toBe(false);
  });
});
