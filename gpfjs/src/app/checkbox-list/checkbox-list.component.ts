import { Component, OnInit, Input } from '@angular/core';
import { AddItem, RemoveItem, SetItems, CheckboxListModel, CheckboxListState } from './checkbox-list.state';

@Component({
  selector: 'gpf-checkbox-list',
  templateUrl: './checkbox-list.component.html',
  styleUrls: ['./checkbox-list.component.css']
})
export class CheckboxListComponent implements OnInit {

  @Input() title: string;
  @Input() stateName: string;
  @Input() items: Set<string>;
  @Input() selectedItems: Set<string>;
  errors: string[];

  constructor() { }

  ngOnInit(): void {
    console.log(this.stateName);
    if (!this.selectedItems) {
      this.selectAll();
    }
  }

  selectNone(): void {
    this.selectedItems.clear();
  }

  selectAll(): void {
    this.selectedItems = new Set([...this.items]);
  }

  toggleItem(item: string) {
    this.selectedItems.has(item) ? this.selectedItems.delete(item) : this.selectedItems.add(item);
    console.log(this.selectedItems);
  }

}
