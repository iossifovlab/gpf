import { Component, EventEmitter, HostListener, Input, OnInit, Output, ViewChild } from '@angular/core';
import { environment } from 'environments/environment';
import { Observable } from 'rxjs';
import { ItemAddEvent } from './item-add-menu';

@Component({
  selector: 'gpf-item-add-menu',
  templateUrl: './item-add-menu.component.html',
  styleUrls: ['./item-add-menu.component.css']
})
export class ItemAddMenuComponent {
  @Input() public id = '';
  @Input() public getItems: (page: number, searchText: string) => Observable<string[]>;
  @Output() public addedItem = new EventEmitter<ItemAddEvent>();

  @ViewChild('searchInput') private searchInput: HTMLInputElement;

  public items: string[] = [];
  public showMenu = false;
  public imgPathPrefix = environment.imgPathPrefix;
  public searchText = '';
  private isInside = false;
  private pageCounter = 0;
  private loadingPage = false;

  public addItem(id: string, item: string): void {
    this.items.splice(this.items.indexOf(item), 1);
    this.addedItem.emit(new ItemAddEvent(id, item));
  }

  public search(value: string): void {
    this.searchText = value;
    this.resetItems();
    this.updateItemsList();
  }

  public updateItemsIfScrolled(searchText: string, tableContainer: HTMLElement): void {
    if (tableContainer.offsetHeight + tableContainer.scrollTop + 200 > tableContainer.scrollHeight) {
      this.updateItemsList();
    }
  }

  public updateItemsList(): void {
    if (!this.loadingPage) {
      this.pageCounter++;
      this.loadingPage = true;
      this.getItems(this.pageCounter, this.searchText).subscribe((res: string[]) => {
        this.items = this.items.concat(res);
        this.loadingPage = false;
      });
    }
  }

  public resetItems(): void {
    this.items = [];
    this.pageCounter = 0;
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
