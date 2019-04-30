import { Output, EventEmitter, Input, Component, ViewContainerRef } from '@angular/core';
import { GpfTableContentHeaderComponent } from '../../component/header.component';
import { GpfTableSubheaderComponent } from '../../component/subheader.component';
import { SortInfo } from '../../table.component';
import { environment } from '../../../../environments/environment';


@Component({
  selector: 'gpf-table-view-header-cell',
  templateUrl: './header-cell.component.html',
  styleUrls: ['./header-cell.component.css']
})
export class GpfTableHeaderCellComponent {
  @Input() columnInfo: GpfTableContentHeaderComponent;
  @Output() sortingInfoChange = new EventEmitter();
  @Input() sortingInfo: SortInfo;

  constructor(private viewContainer: ViewContainerRef) {
  }

  onSortClick(sortBySubcolumn: GpfTableSubheaderComponent) {
    if (!sortBySubcolumn.sortable) {
      return true;
    }
    let sortInfo: SortInfo;
    if (this.sortingInfo && this.sortingInfo.sortBySubcolumn === sortBySubcolumn) {
      sortInfo = new SortInfo(sortBySubcolumn, !this.sortingInfo.sortOrderAsc);
    } else {
      sortInfo = new SortInfo(sortBySubcolumn, true);
    }
    this.sortingInfoChange.emit(sortInfo);
    return true;
  }

  get imgPathPrefix() {
    return environment.imgPathPrefix;
  }
}
