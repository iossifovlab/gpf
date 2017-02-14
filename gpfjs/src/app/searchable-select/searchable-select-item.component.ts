import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'gpf-searchable-select-item',
  templateUrl: './searchable-select-item.component.html',
  styleUrls: ['./searchable-select-item.component.css']
})
export class SearchableSelectItemComponent {
  @Input() caption: string;
  @Input() value: any;
  @Output() select  = new EventEmitter();

  onSelect(event) {
    this.select.emit(this.value);
  }
}
