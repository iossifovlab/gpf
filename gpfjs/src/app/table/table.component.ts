import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren,
  QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver,
  AfterViewInit, Query, ElementRef
} from '@angular/core';

import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Component({
  selector: 'gpf-table-cell',
  templateUrl: './table-cell.component.html'
})
export class GpfTableCellComponent {
  @Input() columnInfo: GpfTableColumnComponent;
  @Input() data: any;
  private nativeElement: any;

  constructor(private viewContainer: ViewContainerRef) {
    this.nativeElement = viewContainer.element.nativeElement
  }

  ngAfterViewInit() {
    this.columnInfo.width = this.nativeElement.getBoundingClientRect().width
  }
}

@Directive({
  selector: '[gpfTableCellContent]'
})
export class GpfTableCellContentDirective {
  constructor(
    readonly templateRef: TemplateRef<any>,
    readonly viewContainer: ViewContainerRef
  ) { }
}

class DefaultComparator {
  constructor(private subcolumn: GpfTableSubheaderComponent) {
  }

  compare(a: any, b: any): Number {
    let leftVal = a[this.subcolumn.field];
    let rightVal = b[this.subcolumn.field];

    if (leftVal == null && rightVal == null) { return 0; }
    if (leftVal == null) { return -1; }
    if (rightVal == null) { return 1; }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }
}

@Component({
  selector: 'gpf-table-cell-content',
  template: '',
})
export class GpfTableCellContentComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() field: string;
  contentTemplateRef: TemplateRef<any>;

  ngAfterContentInit() {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }
}


@Component({
  selector: 'gpf-table-subheader',
  template: '',
})
export class GpfTableSubheaderComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() field: string;
  @Input() header: string;
  @Input() comparator: (leftVal: any, rightVal: any) => number = this.defaultComparator;
  @Input() sortable = true;

  contentTemplateRef: TemplateRef<any>;

  constructor(protected viewContainer: ViewContainerRef) {
  }

  ngAfterContentInit() {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }

  defaultComparator(a: any, b: any): number {
    let leftVal = a[this.field];
    let rightVal = b[this.field];

    if (leftVal == null && rightVal == null) { return 0; }
    if (leftVal == null) { return -1; }
    if (rightVal == null) { return 1; }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }

  sort(data: any, ascending: boolean) {
    data.sort((a, b) => {
      if (ascending) {
        return this.comparator(a, b);
      } else {
        return this.comparator(b, a);
      }
    });
  }

}

@Component({
  selector: 'gpf-table-content-header',
  template: '',
})
export class GpfTableContentHeaderComponent {
  @ContentChildren(GpfTableSubheaderComponent) subcolumnsChildren: QueryList<GpfTableSubheaderComponent>;
  @Input() header: string;

  constructor(viewContainer: ViewContainerRef) {
  }
}

@Component({
  selector: 'gpf-table-column',
  template: '',
})
export class GpfTableColumnComponent {
  @ContentChildren(GpfTableContentHeaderComponent) headerChildren: QueryList<GpfTableContentHeaderComponent>;
  @ContentChildren(GpfTableCellContentComponent) cellContentChildren: QueryList<GpfTableCellContentComponent>;
  @Input() field: string;
  @Input() header: string;
  @Input() sortable = true;
  public width = 0;

  constructor(viewContainer: ViewContainerRef) {
  }
}

export class SortInfo {
  constructor(public sortBySubcolumn: GpfTableSubheaderComponent, public sortOrderAsc: boolean) {
  }
}


@Directive({
  selector: '[gpfTableLegend]'
})
export class GpfTableLegendDirective {
  constructor(
    readonly templateRef: TemplateRef<any>,
    readonly viewContainer: ViewContainerRef
  ) { }
}

@Component({
  selector: 'gpf-table',
  templateUrl: './table.component.html',
  styleUrls: ['./table.component.css']
})
export class GpfTableComponent {
  @ViewChild('table') tableViewChild: any;
  @ViewChildren('rows') rowViewChildren: QueryList<any>;

  @ContentChildren(GpfTableColumnComponent) columnsChildren: QueryList<GpfTableColumnComponent>;
  @ContentChild(GpfTableLegendDirective) legend: GpfTableLegendDirective;
  @Input() dataSource: Array<any>;
  @Input() noScrollOptimization = false;

  private previousSortingInfo: SortInfo;
  private lastRowHeight = 80;
  private drawOutsideVisibleCount = 5;
  private tableTopPosition = 0;

  @HostListener('window:scroll', ['$event'])
  onWindowScroll(event) {
    this.tableTopPosition = this.tableViewChild.nativeElement.getBoundingClientRect().top;

    if (this.rowViewChildren &&
        this.rowViewChildren.last &&
        this.rowViewChildren.last.nativeElement.getBoundingClientRect().height > 0) {
      this.lastRowHeight = this.rowViewChildren.last.nativeElement
        .getBoundingClientRect().height;
    }
  }

  constructor(
    private viewContainer: ViewContainerRef,
    private ref: ChangeDetectorRef
  ) { }

  set sortingInfo(sortingInfo: SortInfo) {
    this.previousSortingInfo = sortingInfo;
    sortingInfo.sortBySubcolumn.sort(this.dataSource, sortingInfo.sortOrderAsc);
  }

  get sortingInfo(): SortInfo {
    return this.previousSortingInfo;
  }

  showFloatingHeader(): boolean {
    return this.tableViewChild.nativeElement.getBoundingClientRect().top < 0;
  }

  getScrollIndices(): Array<number> {
    if (!this.dataSource) {
      return [0, 0];
    }
    let visibleRowCount = Math.ceil(window.innerHeight / this.lastRowHeight);
    let maxRowCountToDraw = this.drawOutsideVisibleCount * 2 + visibleRowCount;

    let startIndex = Math.ceil(-this.tableTopPosition / this.lastRowHeight) - this.drawOutsideVisibleCount;

    // We should display at least maxRowCountToDraw rows, even at the bottom of the page
    let maxStartIndex = this.dataSource.length - maxRowCountToDraw;
    startIndex = Math.min(startIndex , maxStartIndex);

    // Make sure we always start from index 0 or above
    startIndex = Math.max(0, startIndex);

    let endIndex = startIndex + maxRowCountToDraw;
    return [startIndex, endIndex];
  }

  get totalTableHeight(): number {
    if (!this.dataSource) {
      return 0;
    }
    return this.lastRowHeight * this.dataSource.length;
  }

  get beforeDataCellHeight(): number {
    if (this.noScrollOptimization) {
      return 0;
    }
    return this.getScrollIndices()[0] * this.lastRowHeight;
  }

  get visibleData(): Array<any> {
    if (!this.dataSource) {
      return [];
    }
    if (this.noScrollOptimization) {
      return this.dataSource;
    }
    let scrollIndices  = this.getScrollIndices();
    return this.dataSource.slice(scrollIndices[0], scrollIndices[1]);
  }
}
