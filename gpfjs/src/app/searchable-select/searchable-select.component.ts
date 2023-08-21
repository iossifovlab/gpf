import {
  Component, Input, Output, EventEmitter, ViewChild, ContentChild,
  OnChanges, ElementRef, NgZone,
} from '@angular/core';
import { SearchableSelectTemplateDirective } from './searchable-select-template.directive';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'gpf-searchable-select',
  templateUrl: './searchable-select.component.html',
  styleUrls: ['./searchable-select.css']
})
export class SearchableSelectComponent implements OnChanges {
  @Input() public data: Array<any>;
  @Input() public caption: string;
  @Input() public isInGeneBrowser = false;
  @Output() private search = new EventEmitter();
  @ViewChild('searchBox') private searchBox: ElementRef;
  @Output() private selectItem = new EventEmitter();
  @Output() public focusEvent = new EventEmitter();
  @ContentChild(SearchableSelectTemplateDirective) public template: SearchableSelectTemplateDirective;

  public constructor(
    private ngZone: NgZone,
    private route: ActivatedRoute,
    private eRef: ElementRef
  ) {}


  public ngOnChanges(): void {
    if (this.data.length > 0) {
      this.fillDropdown();
    }
  }

  private fillDropdown(): void {
    const dropdown = $('#sets') as any;
    const self = this;
    dropdown.autocomplete({
      minLength: 0,
      delay: 0,
      source: this.data, // here
      select: function(event, ui) {
        self.onSelect(ui.item.value);
        dropdown.trigger('blur');
      },
    }).bind('focus', () => {
      dropdown.autocomplete('search');
    });
  }

  public searchBoxChange(searchFieldValue): void {
    this.search.emit(searchFieldValue);
  }

  public onSelect(value): void {
    this.selectItem.emit(value);
  }
}
