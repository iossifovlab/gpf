import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ItemAddEvent } from './item-add-menu';

import { ItemAddMenuComponent } from './item-add-menu.component';

describe('ItemAddMenuComponent', () => {
  let component: ItemAddMenuComponent;

  beforeEach(() => {
    component = new ItemAddMenuComponent();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // Search tests

  it('should add item', () => {
    component.items = ['item1', 'item2', 'item3'];
    const emitSpy = jest.spyOn(component.addItemEvent, 'emit');

    component.addItem('id1', 'item2');
    expect(component.items).toEqual(['item1', 'item3']);
    expect(emitSpy).toHaveBeenLastCalledWith(new ItemAddEvent('id1', 'item2'))

    component.addItem('id4', 'item1');
    expect(component.items).toEqual(['item3']);
    expect(emitSpy).toHaveBeenLastCalledWith(new ItemAddEvent('id4', 'item1'))
  });

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
