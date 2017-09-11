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

  constructor(private viewContainer: ViewContainerRef) {
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

@Directive({
  selector: '[gpfTableCellHeader]'
})
export class GpfTableCellHeaderDirective {
  constructor(
    readonly templateRef: TemplateRef<any>,
    readonly viewContainer: ViewContainerRef
  ) { }
}


class DefaultComparator {
  constructor(private subcolumn: GpfTableSubcolumnComponent) {
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
  selector: 'gpf-table-subcolumn',
  template: '',
})
export class GpfTableSubcolumnComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @ContentChildren(GpfTableCellHeaderDirective) headerChildren: QueryList<GpfTableCellHeaderDirective>;
  @Input() field: string;
  @Input() header: string;
  @Input() comparator: (leftVal: any, rightVal: any) => number = this.defaultComparator;
  @Input() sortable = true;

  contentTemplateRef: TemplateRef<any>;
  headerTemplateRef: TemplateRef<any>;

  constructor(protected viewContainer: ViewContainerRef) {
  }

  ngAfterContentInit() {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
    if (this.headerChildren.first) {
      this.headerTemplateRef = this.headerChildren.first.templateRef;
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
  selector: 'gpf-table-column',
  template: '',
})
export class GpfTableColumnComponent extends GpfTableSubcolumnComponent {
  @ContentChildren(GpfTableSubcolumnComponent) subcolumnsChildren: QueryList<GpfTableSubcolumnComponent>;

  constructor(viewContainer: ViewContainerRef) {
    super(viewContainer);
  }

}

export class SortInfo {
  constructor(public sortBySubcolumn: GpfTableSubcolumnComponent, public sortOrderAsc: boolean) {
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
export class GpfTableComponent implements AfterViewInit {
  @ViewChild('table') tableViewChild: any;
  @ViewChildren('rows') rowViewChildren: QueryList<any>;
  @ViewChildren('header') tableHeaderViewChildren: QueryList<ElementRef>;
  @ViewChildren('floatingHeader') tableFloatingHeaderViewChildren: QueryList<ElementRef>;

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

  ngAfterViewInit() {
    this.setStaticTableHeaders(
      this.rowViewChildren, this.tableHeaderViewChildren,
      this.tableFloatingHeaderViewChildren
    );
    Observable.combineLatest([
        this.rowViewChildren.changes.filter(elements => !!elements.first),
        this.tableHeaderViewChildren.changes.filter(elements => !!elements.first),
        this.tableFloatingHeaderViewChildren.changes.filter(elements => !!elements.first),
      ])
      .subscribe(
        ([rows, headers, floatingHeaders])  => {
          this.setStaticTableHeaders(rows, headers, floatingHeaders);
      });
  }

  private setStaticTableHeaders(rows, headers, floatingHeaders) {
    if (rows.length === 0 || headers.length === 0  || floatingHeaders.length === 0) {
      return;
    }
    let headersArray = [].slice
      .call(headers.first.nativeElement
        .getElementsByTagName('gpf-table-header'));
    let floatingHeadersArray = [].slice
      .call(floatingHeaders.first.nativeElement
        .getElementsByTagName('gpf-table-header'));

    let lastRow = rows.last.nativeElement;

    let columnsWithWidths: [any, any, number][] = [].slice
      .call(lastRow.getElementsByTagName('gpf-table-cell'))
      .map((tableCell, index) => [
        headersArray[index],
        floatingHeadersArray[index],
        tableCell.getBoundingClientRect().width
      ]);

    columnsWithWidths.map(([header, floatingHeader, width]) => {
      header.style.width = width + 'px';
      floatingHeader.style.width = width + 'px';
    });
  }

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
