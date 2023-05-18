import { Component, Input, Output, OnChanges, AfterViewInit, EventEmitter } from '@angular/core';
import * as $ from 'jquery';
import 'jquery-ui/ui/widgets/autocomplete.js';

@Component({
  selector: 'gpf-dropdown-select',
  templateUrl: './dropdown-select.component.html',
  styleUrls: ['./dropdown-select.component.css']
})
export class DropdownSelectComponent implements OnChanges, AfterViewInit {

  @Input()
  public items: Array<string>;
  // public items: Array<string> = [
  //   "Item 1",
  //   "Item 2",
  //   "Item 3",
  //   "Item 4",
  //   "Item 5",
  //   "Item 1 A",
  //   "Item 2 A",
  //   "Item 3 A",
  //   "Item 4 A",
  //   "Item 5 A",
  //   "Item 1 B",
  //   "Item 2 B",
  //   "Item 3 B",
  //   "Item 4 B",
  //   "Item 5 B",
  // ];

  @Output()
  public selected = new EventEmitter<string>();

  @Output()
  public change = new EventEmitter<string>();

  private initialized = false;

  public ngOnChanges(): void {
    if (this.initialized) {
      ($('#tags') as any).autocomplete("option", "source", this.items);
    }
  }

  public ngAfterViewInit(): void {
    var self = this;
    ($('#tags') as any).autocomplete({
      source: this.items || [],
      select: function() {
        self.selected.emit(this.value);
      },
      search: function() {
        self.change.emit(this.value);
      }
    });
    self.initialized = true;
  }
}
