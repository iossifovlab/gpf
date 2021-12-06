import { Component, Input, Output, EventEmitter } from '@angular/core';
import { GpfTableColumnComponent } from 'app/table/component/column.component';
import { SortInfo } from '../../table.component';

@Component({
  selector: 'gpf-table-view-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class GpfTableHeaderComponent {
  @Input() columns: any;
  @Output() sortingInfoChange = new EventEmitter();
  @Input() sortingInfo: SortInfo;

  get subheadersCount() {
    if (this.columns.first) {
        const length = this.columns.first.headerChildren.length;
        return Array(length).fill(0).map((x, i) => i);
    }
    return [];
  }

  getMaxWidth(column) {
    if(column.columnMaxWidth) {
      return column.columnMaxWidth;
    }
  }

  getWidth(column: GpfTableColumnComponent): string {
    let width: string;

    if (column === null) {
      width = null;
    } else if (column.columnWidth) {
      width = column.columnWidth;
    }

    return width;
  }
}
