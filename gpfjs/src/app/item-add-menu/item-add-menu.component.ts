import { Component, EventEmitter, HostListener, Input, OnChanges, OnInit, Output } from '@angular/core';
import { ItemAddEvent } from './item-add-menu';

@Component({
  selector: 'gpf-item-add-menu',
  templateUrl: './item-add-menu.component.html',
  styleUrls: ['./item-add-menu.component.css']
})
export class ItemAddMenuComponent implements OnChanges {
  @Input() public id = '';
  @Input() public items: string[] = [];
  @Output() public addItemEvent = new EventEmitter<ItemAddEvent>();
  public filteredItems: string[] = [];
  public searchText = '';
  public showMenu = false;
  private isInside = false;

  public ngOnChanges(): void {
    this.filteredItems = this.items;
  }

  public filterItems(substring: string): void {
    this.filteredItems = this.items.filter(item => item.toLowerCase().includes(substring.toLowerCase()));
  }

  public resetSearch(): void {
    this.filteredItems = this.items;
    this.searchText = '';
  }

  public addItem(id: string, item: string): void {
    this.items.splice(this.items.indexOf(item), 1);
    this.addItemEvent.emit(new ItemAddEvent(id, item));
  }

  @HostListener('click')
  public clickInside(): void {
    this.isInside = true;
  }

  @HostListener('document:click')
  public allClicks(): void {
    if (!this.isInside) {
      this.showMenu = false;
    }
    this.isInside = false;
  }
}
