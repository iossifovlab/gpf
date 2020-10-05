import { Component, Input, Output, EventEmitter, ViewChild, QueryList, ContentChild, ViewChildren } from '@angular/core';
import { SearchableSelectTemplateDirective } from './searchable-select-template.directive';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { NgZone } from '@angular/core';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
})
export class SearchableSelectComponent {
  @Input() data: Array<any>;
  @Input() caption: string;
  @Input() enabledFocusOutSelect = false;
  @Output() search  = new EventEmitter();
  @Output() selectItem  = new EventEmitter();
  @ViewChild(NgbDropdown) dropdown: NgbDropdown;
  @ViewChild('searchBox') searchBox: any;
  @ContentChild(SearchableSelectTemplateDirective) template: SearchableSelectTemplateDirective;

  constructor(
    private ngZone: NgZone
  ) {}

  searchBoxChange(searchFieldValue) {
    this.search.emit(searchFieldValue);
  }

  onFocus(event) {
    this.searchBoxChange('');
    event.stopPropagation();

    this.ngZone.run(() => {
      if (!this.dropdown.isOpen()) {
        this.dropdown.open();
      }
    });
    setTimeout(() => {
      this.searchBox.nativeElement.focus();
    });
    this.onSelect(null);
  }

  onSelect(value) {
    this.selectItem.emit(value);
  }

  log(value) {
  }
}
