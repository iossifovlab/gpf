import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnInit {
  @Input() selectedItems: string[];
  @Input() allItems: string[];
  @Input() readonly minSelectCount = 0;
  @Output() applyEvent = new EventEmitter<string[]>();

  private checkUncheckAllButtonName = 'Uncheck all';
  private searchText: String;
  private checkboxDataArray: {id: string; isChecked: boolean}[];

  constructor() { }

  ngOnInit(): void {
    this.checkboxDataArray = this.toCheckboxDataArray(this.allItems);
    if (this.areAllUnchecked(this.checkboxDataArray)) {
      this.checkUncheckAllButtonName = 'Check all';
    }
  }

  toCheckboxDataArray(allItems: string[]) {
    return allItems.map(
      item => ({id: item, isChecked: this.selectedItems.includes(item)})
    );
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
    this.applyEvent.emit(
      this.checkboxDataArray.filter(item => item.isChecked).map(item => item.id)
    );
  }
}
