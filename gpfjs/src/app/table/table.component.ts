import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef, Output, EventEmitter, Input, Directive, Component, OnInit, ContentChildren, QueryList, TemplateRef, ViewContainerRef, ComponentFactoryResolver } from '@angular/core';

@Component({
  selector: 'gpf-table-cell',
  templateUrl: './table-cell.component.html'
})
export class GpfTableCell {
  @Input() columnInfo: GpfTableColumnComponent;
  @Input() data: any;

  constructor(private viewContainer: ViewContainerRef) {
  }
}



@Component({
  selector: 'gpf-table-header',
  templateUrl: './table-header.component.html'
})
export class GpfTableHeader {
  @Input() columnInfo: GpfTableColumnComponent;
  @Output() sortingInfoChange = new EventEmitter();
  @Input() sortingInfo: SortInfo;

  constructor(private viewContainer: ViewContainerRef) {
  }

  onSortClick(sortBySubcolumn: GpfTableSubcolumnComponent) {
    let sortInfo: SortInfo;
    if (this.sortingInfo && this.sortingInfo.sortBySubcolumn == sortBySubcolumn) {
      sortInfo = new SortInfo(sortBySubcolumn, !this.sortingInfo.sortOrderAsc);
    }
    else {
      sortInfo = new SortInfo(sortBySubcolumn, true);
    }
    this.sortingInfoChange.emit(sortInfo);
  }
}




@Directive({
  selector: '[gpf-table-cell-content]'
})
export class GpfTableCellContentDirective {
  constructor(
    readonly templateRef: TemplateRef<any>,
    readonly viewContainer: ViewContainerRef
  ) { }
}

@Directive({
  selector: '[gpf-table-cell-header]'
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

    if (leftVal == null && rightVal == null) return 0;
    if (leftVal == null) return -1;
    if (rightVal == null) return 1;

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

  contentTemplateRef: TemplateRef<any>;
  headerTemplateRef: TemplateRef<any>;

  constructor(protected viewContainer: ViewContainerRef) {
  }

  ngAfterContentInit() {
    if (this.contentChildren.first) this.contentTemplateRef = this.contentChildren.first.templateRef;
    if (this.headerChildren.first) this.headerTemplateRef = this.headerChildren.first.templateRef;
  }

  defaultComparator(a: any, b: any): number {
    let leftVal = a[this.field];
    let rightVal = b[this.field];

    if (leftVal == null && rightVal == null) return 0;
    if (leftVal == null) return -1;
    if (rightVal == null) return 1;

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }

  sort(data: any, ascending: boolean) {
    data.sort((a, b) => {
      if (ascending) {
        return this.comparator(a, b);
      }
      else {
        return this.comparator(b, a);
      }
    });
  }

}


@Component({
  selector: 'gpf-table-column',
  template: '',
  entryComponents: [
    GpfTableHeader
  ]
})
export class GpfTableColumnComponent extends GpfTableSubcolumnComponent {
  @ContentChildren(GpfTableSubcolumnComponent) subcolumnsChildren: QueryList<GpfTableSubcolumnComponent>;

  constructor(viewContainer: ViewContainerRef) {
    super(viewContainer);
  }

}

class SortInfo {
  constructor(public sortBySubcolumn: GpfTableSubcolumnComponent, public sortOrderAsc: boolean) {
  }
}


@Directive({
  selector: '[gpf-table-legend]'
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
  @ViewChild('row') rowViewChild: any;

  @ContentChildren(GpfTableColumnComponent) columnsChildren: QueryList<GpfTableColumnComponent>;
  @ContentChild(GpfTableLegendDirective) legend: GpfTableLegendDirective;
  @Input() dataSource: any;

  private previousSortingInfo: SortInfo;
  private lastRowHeight = 80;
  private drawOutsideVisibleCount = 5;
  private tableTopPosition = 0;

  @HostListener('window:scroll', ['$event'])
  onWindowScroll(event) {
    this.tableTopPosition = this.tableViewChild.nativeElement.getBoundingClientRect().top;
  }

  constructor(private viewContainer: ViewContainerRef, private ref: ChangeDetectorRef) {
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
    let visibleRowCount = window.innerHeight/this.calculateRowHeight();
    let maxRowCountToDraw = this.drawOutsideVisibleCount * 2 + visibleRowCount

    let startIndex = Math.ceil(Math.max(0, -this.tableTopPosition/this.calculateRowHeight()));
    startIndex =  Math.min(Math.max(0, startIndex - this.drawOutsideVisibleCount), this.dataSource.length - maxRowCountToDraw);
    let endIndex = startIndex + maxRowCountToDraw;
    return [startIndex, endIndex];
  }

  calculateRowHeight(): number {
    if (this.rowViewChild && this.rowViewChild.nativeElement.getBoundingClientRect().height > 0) {
      this.lastRowHeight = this.rowViewChild.nativeElement.getBoundingClientRect().height;
    }

    return this.lastRowHeight;
  }

  get totalTableHeight(): number {
    return this.calculateRowHeight() * this.dataSource.length;
  }

  get beforeDataCellHeight(): number {
    return this.getScrollIndices()[0] * this.calculateRowHeight();
  }

  get visibleData(): any {
    let scrollIndices  = this.getScrollIndices();
    return this.dataSource.slice(scrollIndices[0], scrollIndices[1]);
  }
}
