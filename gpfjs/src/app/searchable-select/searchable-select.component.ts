import {
  Component, Input, Output, EventEmitter, ViewChild, ContentChild,
  AfterViewInit, OnChanges, ElementRef, NgZone, HostListener
} from '@angular/core';
import { SearchableSelectTemplateDirective } from './searchable-select-template.directive';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
  styleUrls: ['./searchable-select.component.css']
})
export class SearchableSelectComponent implements AfterViewInit, OnChanges {
  @Input() public data: Array<any>;
  @Input() public caption: string;
  @Input() public isInGeneBrowser = false;
  @Input() public showLoadingSpinner: boolean;
  @Input() private hideDropdown: boolean;
  @Output() private search = new EventEmitter();
  @Output() private selectItem = new EventEmitter();
  @Output() public focusEvent = new EventEmitter();
  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;
  @ViewChild('searchBox') private searchBox: ElementRef;
  @ContentChild(SearchableSelectTemplateDirective) public template: SearchableSelectTemplateDirective;

  @HostListener('document:click', ['$event'])
  public clickout(event): void {
    if (!this.eRef.nativeElement.contains(event.target)) {
      this.dropdown.close();
    }
  }

  public onEnterPress(): void {
    if (this.isInGeneBrowser) {
      this.onSelect(this.searchBox.nativeElement.value);
      this.dropdown.close();
    }
  }

  public constructor(
    private ngZone: NgZone,
    private route: ActivatedRoute,
    private eRef: ElementRef
  ) {}

  public ngOnChanges(): void {
    if (this.hideDropdown) {
      this.dropdown.close();
    }
  }

  public ngAfterViewInit(): void {
    this.dropdown.autoClose = 'inside';
  }

  public searchBoxChange(searchFieldValue): void {
    this.search.emit(searchFieldValue);
  }

  public onFocus(event): void {
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
    this.focusEvent.emit();
  }

  public onSelect(value): void {
    this.selectItem.emit(value);
  }
}
