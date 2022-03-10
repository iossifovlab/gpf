import { Component, Input, Output, EventEmitter, ViewChild, ContentChild, AfterViewInit, OnChanges, ElementRef } from '@angular/core';
import { SearchableSelectTemplateDirective } from './searchable-select-template.directive';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { NgZone } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
})
export class SearchableSelectComponent implements AfterViewInit, OnChanges {
  @Input() public data: Array<any>;
  @Input() public caption: string;
  @Input() public isInGeneBrowser = false;
  @Input() private hideDropdown: boolean;
  @Output() private search  = new EventEmitter();
  @Output() private selectItem  = new EventEmitter();
  @Output() public onFocusEvent = new EventEmitter();
  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;
  @ViewChild('searchBox') private searchBox: ElementRef;
  @ContentChild(SearchableSelectTemplateDirective) public template: SearchableSelectTemplateDirective;

  public onEnterPress() {
    if (this.isInGeneBrowser) {
      this.onSelect(this.searchBox.nativeElement.value);
      this.dropdown.close();
    }
  }

  constructor(
    private ngZone: NgZone,
    private route: ActivatedRoute,
  ) {}

  public ngOnChanges(): void {
    if (this.hideDropdown) {
      this.dropdown.close();
    }
  }

  public ngAfterViewInit(): void {
    // temporary solution, fix along side issue GPF-1102
    if (!(this.isInGeneBrowser && this.route.snapshot.params.gene)) {
      this.focusSearchBox();
    }

    this.dropdown.autoClose = 'inside';
  }

  public searchBoxChange(searchFieldValue) {
    this.search.emit(searchFieldValue);
  }

  public onFocus(event) {
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
    this.onFocusEvent.emit();
  }

  public onSelect(value) {
    this.selectItem.emit(value);
  }

  /**
  * Waits search box element to load.
  * @returns promise
  */
  private async waitForSearchBoxToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchBox !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 200);
    });
  }

  private focusSearchBox() {
    this.waitForSearchBoxToLoad().then(() => {
      this.searchBox.nativeElement.focus();
    });
  }
}
