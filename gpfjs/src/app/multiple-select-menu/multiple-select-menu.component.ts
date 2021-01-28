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

  apply() {
    this.applyEvent.emit(
      this.checkboxDataArray.filter(item => item.isChecked).map(item => item.id)
    );
  }

}
