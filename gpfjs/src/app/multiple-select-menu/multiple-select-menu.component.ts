import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

@Component({
  selector: 'gpf-multiple-select-menu',
  templateUrl: './multiple-select-menu.component.html',
  styleUrls: ['./multiple-select-menu.component.css']
})
export class MultipleSelectMenuComponent implements OnInit {
  @Input() selectedItems: string[];
  @Input() allItems: string[];
  @Output() applyEvent = new EventEmitter<string[]>();

  private checkboxDataArray: {id: string; isChecked: boolean}[];
  private checkUncheckAll = 'Uncheck all';

  constructor() { }

  ngOnInit(): void {
    this.checkboxDataArray = this.toCheckboxDataArray(this.allItems);
    console.log(this.checkboxDataArray);
  }

  toCheckboxDataArray(allItems: string[]) {
    return allItems.map(
      item => ({id: item, isChecked: this.selectedItems.includes(item)})
    );
  }

  toggleCheckingAll() {
    if (this.checkUncheckAll === 'Uncheck all') {
      this.checkboxDataArray.forEach(item => item.isChecked = false);
      this.checkUncheckAll = 'Check all';
    } else if (this.checkUncheckAll === 'Check all') {
      this.checkboxDataArray.forEach(item => item.isChecked = true);
      this.checkUncheckAll = 'Uncheck all';
    }
  }

  apply() {
    this.applyEvent.emit(
      this.checkboxDataArray.filter(item => item.isChecked).map(item => item.id)
    );
  }
}
