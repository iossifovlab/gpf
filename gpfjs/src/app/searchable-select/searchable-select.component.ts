import { Component, Input, Output, EventEmitter, ViewChild, ContentChild, AfterViewInit, OnChanges } from '@angular/core';
import { SearchableSelectTemplateDirective } from './searchable-select-template.directive';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { NgZone } from '@angular/core';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
})
export class SearchableSelectComponent implements AfterViewInit, OnChanges {
  @Input() data: Array<any>;
  @Input() caption: string;
  @Input() isInGeneBrowser = false;
  @Input() hideDropdown: boolean;
  @Output() search  = new EventEmitter();
  @Output() selectItem  = new EventEmitter();
  @ViewChild(NgbDropdown) dropdown: NgbDropdown;
  @ViewChild('searchBox') searchBox: any;
  @ContentChild(SearchableSelectTemplateDirective) template: SearchableSelectTemplateDirective;

  onEnterPress() {
    if (this.isInGeneBrowser) {
      this.onSelect(this.searchBox.nativeElement.value);
      this.dropdown.close();
    }
  }

  constructor(
    private ngZone: NgZone
  ) {}

  ngOnChanges(): void {
    if (this.hideDropdown) {
      this.dropdown.close();
    }
  }

  ngAfterViewInit(): void {
    this.dropdown.autoClose = 'inside';
  }

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
    this.onSelect('');
  }

  onSelect(value) {
    this.selectItem.emit(value);
  }
}
