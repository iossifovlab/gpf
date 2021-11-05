import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import { cloneDeep } from 'lodash';

interface MenuItem {
  id: string;
  isChecked: boolean;
}

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnInit, OnChanges {
  @Input() public menuId: string;
  @Input() public selectedItems: string[];
  @Input() public allItems: string[];
  @Input() public readonly minSelectCount = 0;
  @Output() public applyEvent = new EventEmitter<{menuId: string, selectedItems: string[], order: string[]}>();
  @ViewChild('searchInput') public searchInput: ElementRef;

  public checkUncheckAllButtonName = 'Uncheck all';
  public searchText: string;
  public checkboxDataArray: MenuItem[];
  private checkboxDataArraySavedState: MenuItem[];

  public ngOnChanges(): void {
    this.checkboxDataArraySavedState = this.toCheckboxDataArray(this.allItems);
    this.applySavedState();
    this.searchText = '';
  }

  public ngOnInit(): void {
    this.checkboxDataArraySavedState = this.toCheckboxDataArray(this.allItems);
    this.applySavedState();

    if (this.areAllUnchecked(this.checkboxDataArraySavedState)) {
      this.checkUncheckAllButtonName = 'Check all';
    }
  }

  public toggleCheckingAll(): void {
    if (this.checkUncheckAllButtonName === 'Uncheck all') {
      this.checkboxDataArray.forEach(item => {
        item.isChecked = false;
      });
      this.checkUncheckAllButtonName = 'Check all';
    } else if (this.checkUncheckAllButtonName === 'Check all') {
      this.checkboxDataArray.forEach(item => {
        item.isChecked = true;
      });
      this.checkUncheckAllButtonName = 'Uncheck all';
    }
  }

  public isSelectionValid(): boolean {
    return this.checkboxDataArray.filter(item => item.isChecked === true).length >= this.minSelectCount;
  }

  public apply(): void {
    this.updateSavedState();

    this.applyEvent.emit({
      menuId: this.menuId,
      selectedItems: this.checkboxDataArray.filter(item => item.isChecked).map(item => item.id),
      order: this.allItems
    });
  }

  public focusSearchInput(): void {
    this.waitForSearchInputToLoad().then(() => {
      this.searchInput.nativeElement.focus();
    });
  }

  public drop(event: CdkDragDrop<string[]>): void {
    moveItemInArray(this.checkboxDataArray, event.previousIndex, event.currentIndex);
    moveItemInArray(this.allItems, event.previousIndex, event.currentIndex);
  }

  private toCheckboxDataArray(allItems: string[]): MenuItem[] {
    return allItems.map(item => ({ id: item, isChecked: this.selectedItems.includes(item) }));
  }

  private applySavedState(): void {
    this.checkboxDataArray = cloneDeep(this.checkboxDataArraySavedState);
  }

  private updateSavedState(): void {
    this.checkboxDataArraySavedState = cloneDeep(this.checkboxDataArray);
  }

  private areAllUnchecked(checkboxDataArray: MenuItem[]): boolean {
    return !checkboxDataArray.map(item => item.isChecked).includes(true);
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
}
