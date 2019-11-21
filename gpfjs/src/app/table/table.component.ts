import { ContentChild, ViewChildren, ViewChild, HostListener, ChangeDetectorRef,
  Input, Component, ContentChildren, QueryList, ViewContainerRef
} from '@angular/core';

import { GpfTableColumnComponent } from './component/column.component';
import { GpfTableSubheaderComponent } from './component/subheader.component';
import { GpfTableLegendDirective } from './component/legend.directive';

export class SortInfo {
  constructor(public sortBySubcolumn: GpfTableSubheaderComponent, public sortOrderAsc: boolean) {
  }
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

  showFloatingHeader: boolean;

  @HostListener('window:scroll', ['$event'])
  onWindowScroll(event) {
    this.tableTopPosition = this.tableViewChild.nativeElement.getBoundingClientRect().top;

    if (this.rowViewChildren &&
        this.rowViewChildren.last &&
        this.rowViewChildren.last.nativeElement.getBoundingClientRect().height > 0) {
      this.lastRowHeight = this.rowViewChildren.last.nativeElement
        .getBoundingClientRect().height;
    }

    this.showFloatingHeader = this.tableTop();
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

  tableTop(): boolean {
    return this.tableViewChild.nativeElement.getBoundingClientRect().top < 0;
  }

  getScrollIndices(): Array<number> {
    if (!this.dataSource) {
      return [0, 0];
    }
    const visibleRowCount = Math.ceil(window.innerHeight / this.lastRowHeight);
    const maxRowCountToDraw = this.drawOutsideVisibleCount * 2 + visibleRowCount;

    let startIndex = Math.ceil(-this.tableTopPosition / this.lastRowHeight) - this.drawOutsideVisibleCount;

    // We should display at least maxRowCountToDraw rows, even at the bottom of the page
    const maxStartIndex = this.dataSource.length - maxRowCountToDraw;
    startIndex = Math.min(startIndex , maxStartIndex);

    // Make sure we always start from index 0 or above
    startIndex = Math.max(0, startIndex);

    const endIndex = startIndex + maxRowCountToDraw;
    return [startIndex, endIndex];
  }

  get beforeDataCellHeight(): number {
    if (this.noScrollOptimization) {
      return 0;
    }
    return this.getScrollIndices()[0] * this.lastRowHeight;
  }

  get afterDataCellHeight(): number {
    if (this.noScrollOptimization || !this.dataSource) {
      return 0;
    }
    return (this.dataSource.length - this.getScrollIndices()[1]) * this.lastRowHeight;
  }

  get visibleData(): Array<any> {
    if (!this.dataSource) {
      return [];
    }
    if (this.noScrollOptimization) {
      return this.dataSource;
    }
    const scrollIndices  = this.getScrollIndices();
    return this.dataSource.slice(scrollIndices[0], scrollIndices[1]);
  }

  // This function is used to calculate the 'min-width' style attribute for the
  // '.table-header-sticky-div' wrapper, used for resizing the div properly.
  calculateMinWidth(columns): number {
    let totalWidth = 0;

    // Iterates through the columns._result array, which contains the column's widths.
    // Removes the 'px' from the end of each columnWidth, converts it to a number,
    // and adds it to 'totalWidth'
    for (const column of columns._results) {
      totalWidth += Number(column.columnWidth.substring(0, column.columnWidth.length - 2));
    }

    return totalWidth + 5;
  }
}
