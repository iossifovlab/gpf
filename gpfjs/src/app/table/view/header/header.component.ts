import { Component, Input, Output, EventEmitter } from '@angular/core';
import { GpfTableColumnComponent } from '../../component/column.component'
import { SortInfo } from '../../table.component'


@Component({
  selector: 'gpf-table-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css']
})
export class GpfTableHeaderComponent {
  @Input() columns: any;
  @Output() sortingInfoChange = new EventEmitter();
  @Input() sortingInfo: SortInfo;

  get subheadersCount() {
      if (this.columns.first) {
          let length = this.columns.first.headerChildren.length;
          return Array(length).fill(0).map((x, i) => i)
      }
      return [];
  }
}
