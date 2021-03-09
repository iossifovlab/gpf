import { Component, ElementRef, EventEmitter, Input, OnChanges, OnInit, Output, ViewChild } from '@angular/core';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnInit, OnChanges {
  @Input() id: string;
  @Input() selectedItems: string[];
  @Input() allItems: string[];
  @Input() readonly minSelectCount = 0;
  @Output() applyEvent = new EventEmitter<{id: string, data: string[]}>();
  @Input() focusInput: boolean;
  @ViewChild('searchInput') searchInput: ElementRef;

  private checkUncheckAllButtonName = 'Uncheck all';
  private searchText: String;
  private checkboxDataArray: {id: string; isChecked: boolean}[];

  constructor() { }

  ngOnChanges(): void {
    if (this.focusInput) {
      this.focusSearchInput();
    }
  }

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
    this.applyEvent.emit({
      id: this.id,
      data: this.checkboxDataArray.filter(item => item.isChecked).map(item => item.id)
    });
  }

  focusSearchInput() {
    setTimeout(() => {
      this.searchInput.nativeElement.focus();
    }, 0); 
  }
}
