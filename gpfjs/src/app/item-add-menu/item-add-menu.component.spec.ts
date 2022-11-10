import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ItemAddEvent } from './item-add-menu';

import { ItemAddMenuComponent } from './item-add-menu.component';

describe('ItemAddMenuComponent', () => {
  let component: ItemAddMenuComponent;
  let fixture: ComponentFixture<ItemAddMenuComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [
        ItemAddMenuComponent,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ItemAddMenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should add item', () => {
    component.items = ['item1', 'item2', 'item3'];
    const emitSpy = jest.spyOn(component.addedItem, 'emit');

    component.addItem('id1', 'item2');
    expect(component.items).toStrictEqual(['item1', 'item3']);
    expect(emitSpy).toHaveBeenLastCalledWith(new ItemAddEvent('id1', 'item2'));

    component.addItem('id4', 'item1');
    expect(component.items).toStrictEqual(['item3']);
    expect(emitSpy).toHaveBeenLastCalledWith(new ItemAddEvent('id4', 'item1'));
  });

  // it('should request item list update when list is scrolled', () => {
  //   const neededMoreItemsEmitSpy = jest.spyOn(component.neededMoreItems, 'emit');
  //   const button = fixture.debugElement.query(By.css('.add-button'));

  //   button.triggerEventHandler('click', {});
  //   fixture.detectChanges();

  //   const tableContainer = fixture.debugElement.query(By.css('.menu'));
  //   tableContainer.triggerEventHandler('scroll', {});

  //   expect(neededMoreItemsEmitSpy).toHaveBeenCalledWith();
  // });

  it('should close menu when clicking outside', () => {
    // Simulate opening the menu
    component.showMenu = true;

    // Simulate click inside the menu
    component.clickInside();
    component.allClicks();

    expect(component.showMenu).toBe(true);

    // Simulate click outside the menu
    component.allClicks();

    expect(component.showMenu).toBe(false);
  });
});
