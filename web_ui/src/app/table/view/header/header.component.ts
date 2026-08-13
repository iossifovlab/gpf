import {
  Component, Input, Output, EventEmitter, ChangeDetectionStrategy, HostListener, ChangeDetectorRef,
  QueryList, inject
} from '@angular/core';
import { SortInfo } from '../../table.component';
import { GpfTableColumnComponent } from '../../component/column.component';

@Component({
  selector: 'gpf-table-view-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  standalone: false
})
export class GpfTableHeaderComponent {
  private cdr = inject(ChangeDetectorRef);

  @Input() public columns: QueryList<GpfTableColumnComponent>;
  @Output() public sortingInfoChange = new EventEmitter<SortInfo>();
  @Input() public sortingInfo: SortInfo;

  @HostListener('window:resize')
  public onWindowResize(): void {
    this.cdr.detectChanges();
  }

  public get subheadersCount(): number[] {
    if (this.columns.first) {
      const length: number = this.columns.first.headerChildren.length;
      return Array(length).fill(0).map((x, i) => i);
    }
    return [];
  }
}
