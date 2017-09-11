import { Component, Input, Output, EventEmitter } from '@angular/core';
import { GpfTableColumnComponent, SortInfo } from '../table.component'


@Component({
  selector: 'gpf-table-header',
  templateUrl: './table-header.component.html',
  styleUrls: ['./table-header.component.css']
})
export class GpfTableHeaderComponent {
  @Input() columns: GpfTableColumnComponent[];
  @Output() sortingInfoChange = new EventEmitter();
  @Input() sortingInfo: SortInfo;
}
