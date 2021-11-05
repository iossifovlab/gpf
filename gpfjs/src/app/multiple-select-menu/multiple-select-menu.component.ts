import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';
import {cloneDeep} from 'lodash';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css'],
})
export class MultipleSelectMenuComponent implements OnInit, OnChanges {
  @Input() menuId: string;
  @Input() selectedItems: string[];
  @Input() allItems: string[];
  @Input() readonly minSelectCount = 0;
  @Output() applyEvent = new EventEmitter<{menuId: string, data: string[]}>();
  @ViewChild('searchInput') searchInput: ElementRef;

  checkUncheckAllButtonName = 'Uncheck all';
  searchText: String;
  checkboxDataArray: {id: string; isChecked: boolean}[];
  checkboxDataArraySavedState: {id: string; isChecked: boolean}[];

  constructor() { }

  ngOnChanges(): void {
    this.checkboxDataArraySavedState = this.toCheckboxDataArray(this.allItems);
    this.applySavedState();
    this.searchText = '';
  }

  ngOnInit(): void {
    this.checkboxDataArraySavedState = this.toCheckboxDataArray(this.allItems);
    this.applySavedState();

    if (this.areAllUnchecked(this.checkboxDataArraySavedState)) {
      this.checkUncheckAllButtonName = 'Check all';
    }
  }

  toCheckboxDataArray(allItems: string[]) {
    return allItems.map(
      item => ({id: item, isChecked: this.selectedItems.includes(item)})
    );
  }

  applySavedState() {
    this.checkboxDataArray = cloneDeep(this.checkboxDataArraySavedState);
  }

  updateSavedState() {
    this.checkboxDataArraySavedState = cloneDeep(this.checkboxDataArray);
  }

  areAllUnchecked(checkboxDataArray): boolean {
    return !checkboxDataArray.map(item => item.isChecked).includes(true);
  }

  toggleCheckingAll() {
    if (this.checkUncheckAllButtonName === 'Uncheck all') {
      this.checkboxDataArray.forEach(item => item.isChecked = false);
      this.checkUncheckAllButtonName = 'Check all';
    } else if (this.checkUncheckAllButtonName === 'Check all') {
      this.checkboxDataArray.forEach(item => item.isChecked = true);
      this.checkUncheckAllButtonName = 'Uncheck all';
    }
  }

  isSelectionValid() {
    return this.checkboxDataArray.filter(item => item.isChecked === true).length >= this.minSelectCount;
  }

  apply() {
    this.updateSavedState();

    this.applyEvent.emit({
      menuId: this.menuId,
      data: this.checkboxDataArray.filter(item => item.isChecked).map(item => item.id)
    });
  }

  /**
  * Waits search input element to load.
  * @returns promise
  */
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

  focusSearchInput() {
    this.waitForSearchInputToLoad().then(() => {
      this.searchInput.nativeElement.focus();
    });
  }

  drop(event: CdkDragDrop<string[]>) {
    console.log(this.checkboxDataArray);
    console.log(event);
    moveItemInArray(this.checkboxDataArray, event.previousIndex, event.currentIndex);
    console.log(this.checkboxDataArray);
  }
}
