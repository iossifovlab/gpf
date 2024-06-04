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
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  @Input() public data: Array<any>;
  @Input() public caption: string;
  @Input() public isInGeneBrowser = false;
  @Input() public showLoadingSpinner: boolean;
  @Input() private hideDropdown: boolean;
  @Output() private search = new EventEmitter();
  @Output() private selectItem = new EventEmitter();
  @Output() public focusEvent = new EventEmitter();
  // @ViewChild(NgbDropdown) private dropdown: NgbDropdown;
  @ViewChild('searchBox') private searchBox: ElementRef;
  @ContentChild(SearchableSelectTemplateDirective) public template: SearchableSelectTemplateDirective;

  @HostListener('document:click', ['$event'])
  public clickout(event): void {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-argument
    if (!(this.eRef.nativeElement as HTMLElement).contains(event.target)) {
      // this.dropdown.close();
    }
  }

  public onEnterPress(): void {
    if (this.isInGeneBrowser) {
      this.onSelect((this.searchBox.nativeElement as HTMLInputElement).value);
      // this.dropdown.close();
    }
  }

  public constructor(
    private ngZone: NgZone,
    private route: ActivatedRoute,
    private eRef: ElementRef
  ) {}

  public ngOnChanges(): void {
    if (this.hideDropdown) {
      // this.dropdown.close();
    }
  }

  public ngAfterViewInit(): void {
    // this.dropdown.autoClose = 'inside';
  }

  public searchBoxChange(searchFieldValue): void {
    this.search.emit(searchFieldValue);
  }

  public onFocus(event: Event): void {
    this.searchBoxChange('');
    event.stopPropagation();

    // this.ngZone.run(() => {
    //   if (!this.dropdown.isOpen()) {
    //     this.dropdown.open();
    //   }
    // });
    setTimeout(() => {
      (this.searchBox.nativeElement as HTMLInputElement).focus();
    });
    this.onSelect(null);
    this.focusEvent.emit();
  }

  public onSelect(value): void {
    this.selectItem.emit(value);
  }
}
