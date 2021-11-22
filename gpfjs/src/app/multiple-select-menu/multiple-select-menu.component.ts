import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import { ItemApplyEvent } from './multiple-select-menu';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnInit, OnChanges {
  @Input() public menuId: string;
  @Input() public itemsSource: { itemIds: string[]; shownItemIds: string[]; };
  @Output() public applyEvent = new EventEmitter<ItemApplyEvent>();
  @ViewChild('searchInput') public searchInput: ElementRef;

  public allItems: string[];
  public filteredItems: string[];
  public selectedItems: Set<string>;

  public checkUncheckAllButtonName = 'Uncheck all';
  public searchText: string;

  public ngOnChanges(): void {
    this.searchText = '';
    this.allItems = this.itemsSource.itemIds;
    this.filteredItems = this.allItems;
    this.selectedItems = new Set(this.itemsSource.shownItemIds);
  }

  public refresh(): void {
    this.allItems = this.itemsSource.itemIds;
    this.filteredItems = this.allItems;
    this.selectedItems = new Set(this.itemsSource.shownItemIds);
    this.focusSearchInput();
  }

  public ngOnInit(): void {
    if (!this.selectedItems.size) {
      this.checkUncheckAllButtonName = 'Check all';
    }
  }

  private async waitForSearchInputToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  public toggleCheckingAll(): void {
    if (this.checkUncheckAllButtonName === 'Uncheck all') {
      this.selectedItems = new Set();
      this.checkUncheckAllButtonName = 'Check all';
    } else if (this.checkUncheckAllButtonName === 'Check all') {
      this.selectedItems = new Set(this.allItems);
      this.checkUncheckAllButtonName = 'Uncheck all';
    }
  }

  public toggleItem(item: string, $event: Event) {
    if(!($event.target instanceof HTMLInputElement)) {
      return;
    }
    if ($event.target.checked) {
      this.selectedItems.add(item);
    } else {
      this.selectedItems.delete(item);
    }
  }

  public apply(): void {
    this.applyEvent.emit({
      menuId: this.menuId,
      selected: Array.from(this.selectedItems),
      order: this.allItems,
    });
  }

  public focusSearchInput(): void {
    this.waitForSearchInputToLoad().then(() => {
      this.searchInput.nativeElement.focus();
    });
  }

  public drop(event: CdkDragDrop<string[]>): void {
    moveItemInArray(this.allItems, event.previousIndex, event.currentIndex);
  }

  public filterItems(substring): void {
    this.filteredItems = this.allItems.filter(item => item.toLowerCase().includes(substring.toLowerCase()));
  }
}
