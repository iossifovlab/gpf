import { Component, Input, Output, EventEmitter, ChangeDetectionStrategy, HostListener } from '@angular/core';
import { SortInfo } from '../../table.component';

@Component({
  selector: 'gpf-table-view-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class GpfTableHeaderComponent {
  @Input() public columns: any;
  @Output() public sortingInfoChange = new EventEmitter();
  @Input() public sortingInfo: SortInfo;

  public get subheadersCount(): number[] {
    if (this.columns.first) {
      const length: number = this.columns.first.headerChildren.length;
      return Array(length).fill(0).map((x, i) => i);
    }
    return [];
  }
}
