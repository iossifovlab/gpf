import { Component, EventEmitter, HostListener, Input, Output, ViewChild } from '@angular/core';
import { environment } from 'environments/environment';
import { Observable, Subscription, debounceTime } from 'rxjs';
import { Item } from './item-add-menu';

@Component({
  selector: 'gpf-item-add-menu',
  templateUrl: './item-add-menu.component.html',
  styleUrls: ['./item-add-menu.component.css'],
  standalone: false
})
export class ItemAddMenuComponent {
  @Input() public getItems: (page: number, searchText: string) => Observable<Item[]>;
  @Output() public addedItem = new EventEmitter<Item>();

  @ViewChild('searchInput') private searchInput: HTMLInputElement;

  public items: Item[] = [];
  public showMenu = false;
  public imgPathPrefix = environment.imgPathPrefix;
  public searchText = '';
  private isInside = false;
  private pageCounter = 1;
  private itemSubscription = new Subscription();
  private finalParams: {page: number; searchText: string} = {page: undefined, searchText: undefined};

  public addItem(item: Item): void {
    this.items.splice(this.items.indexOf(item), 1);
    this.addedItem.emit(item);
  }

  public search(value: string): void {
    this.searchText = value;
    this.items = [];
    this.pageCounter = 1;
    this.updateItemsList();
  }

  public updateItemsIfScrolled(searchText: string, tableContainer: HTMLElement): void {
    if (this.itemSubscription.closed
      && tableContainer.offsetHeight + tableContainer.scrollTop + 200 > tableContainer.scrollHeight
    ) {
      this.updateItemsList();
    }
  }

  private updateItemsList(): void {
    if (
      this.showMenu
      && (this.pageCounter !== this.finalParams.page
      || this.searchText !== this.finalParams.searchText)
    ) {
      this.itemSubscription.unsubscribe();
      this.itemSubscription = this.getItems(this.pageCounter, this.searchText)
        .pipe(
          debounceTime(300)
        ).subscribe((res: Item[]) => {
          if (res.length) {
            this.pageCounter++;
            this.items = this.items.concat(res);
            document.getElementById('menu').scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
          } else {
            this.finalParams.page = this.pageCounter;
            this.finalParams.searchText = this.searchText;
          }
        });
    }
  }

  @HostListener('click')
  public clickInside(): void {
    this.isInside = true;
  }

  @HostListener('document:click')
  public allClicks(): void {
    if (!this.isInside) {
      this.showMenu = false;
      this.finalParams = {page: undefined, searchText: undefined};
    }
    this.isInside = false;
  }

  @HostListener('document:keydown.escape')
  public onEscapeButtonPress(): void {
    this.showMenu = false;
    this.finalParams = {page: undefined, searchText: undefined};
  }
}
