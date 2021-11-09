import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnInit, OnChanges {
  @Input() public menuId: string;
  @Input() public itemsSource;
  @Output() public applyEvent = new EventEmitter<{menuId: string, selected: string[], order: string[]}>();
  @ViewChild('searchInput') public searchInput: ElementRef;

  public allItems: string[];
  public selectedItems: Set<string>;

  public checkUncheckAllButtonName = 'Uncheck all';
  public searchText: string;

  public ngOnChanges(): void {
    this.searchText = '';
    this.allItems = this.itemsSource.itemIds;
    console.log('123123');
    this.selectedItems = new Set(this.itemsSource.shownItemIds);
  }

  public refresh(): void {
    console.log('weqeqwe');
    this.allItems = this.itemsSource.itemIds;
    if (this.itemsSource.shownItemIds.length) {
      this.selectedItems = new Set(this.itemsSource.shownItemIds);
    } else {
      this.selectedItems = new Set(this.allItems);
    }
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

  public toggleItem(item: string, event) {
    if (event.target.checked) {
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
}
