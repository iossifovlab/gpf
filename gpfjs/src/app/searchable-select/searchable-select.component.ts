import { Component, Input, Output, EventEmitter, ViewChild, ContentChild } from '@angular/core';
import { SearchableSelectTemplateDirective } from './searchable-select-template.directive';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
})
export class SearchableSelectComponent {
  @Input() data: Array<any>;
  @Input() caption: string;
  @Output() search  = new EventEmitter();
  @Output() selectItem  = new EventEmitter();
  @ViewChild("inputGroup") inputGroupSpan: any;
  @ContentChild(SearchableSelectTemplateDirective) template: SearchableSelectTemplateDirective;

  searchBoxChange(searchFieldValue) {
    this.search.emit(searchFieldValue);
  }

  onFocus(event) {
    event.stopPropagation();
    this.inputGroupSpan.nativeElement.classList.add("show");
  }

  onSelect(value) {
    this.selectItem.emit(value);
  }
}
