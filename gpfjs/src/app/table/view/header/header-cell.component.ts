import { Output, EventEmitter, Input, Component } from '@angular/core';
import { GpfTableContentHeaderComponent } from '../../component/header.component';
import { GpfTableSubheaderComponent } from '../../component/subheader.component';
import { SortInfo } from '../../table.component';
import { environment } from '../../../../environments/environment';

@Component({
    selector: 'gpf-table-view-header-cell',
    templateUrl: './header-cell.component.html',
    styleUrls: ['./header-cell.component.css'],
    standalone: false
})
export class GpfTableHeaderCellComponent {
  @Input() public columnInfo: GpfTableContentHeaderComponent;
  @Output() public sortingInfoChange = new EventEmitter();
  @Input() public sortingInfo: SortInfo;
  public imgPathPrefix = environment.imgPathPrefix;

  public onSortClick(sortBySubcolumn: GpfTableSubheaderComponent): boolean {
    if (!sortBySubcolumn.sortable) {
      return;
    }

    let sortInfo: SortInfo;
    if (this.sortingInfo && this.sortingInfo.sortBySubcolumn === sortBySubcolumn) {
      sortInfo = new SortInfo(sortBySubcolumn, !this.sortingInfo.sortOrderAsc);
    } else {
      sortInfo = new SortInfo(sortBySubcolumn, false);
    }

    this.sortingInfoChange.emit(sortInfo);

    return true;
  }
}
