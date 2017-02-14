import { Component, Input, Output, EventEmitter, ViewChild } from '@angular/core';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
})
export class SearchableSelectComponent {
  @Input() caption: string;
  @Output() searchTerm  = new EventEmitter();
  @ViewChild("inputGroup") inputGroupSpan: any;

  search(searchFieldValue) {
    this.searchTerm.emit(searchFieldValue);
  }

  onFocus(event) {
    event.stopPropagation();
    this.inputGroupSpan.nativeElement.classList.add("show");
  }
}
