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
  @ViewChild('inputGroup') inputGroupSpan: any;
  @ViewChild('searchBox') searchBox: any;
  @ContentChild(SearchableSelectTemplateDirective) template: SearchableSelectTemplateDirective;

  searchBoxChange(searchFieldValue) {
    this.search.emit(searchFieldValue);
  }

  onFocus(event) {
    event.stopPropagation();
    setTimeout(() => {
      this.searchBox.nativeElement.focus();
      this.inputGroupSpan.nativeElement.classList.add('show');
    });
    this.onSelect(null);
  }

  onSelect(value) {
    this.selectItem.emit(value);
  }

  log(value) {
  }
}
