import { Input, Component } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component';
import { GpfTableContentComponent } from '../component/content.component';

@Component({
  selector: 'gpf-table-view-cell',
  templateUrl: './cell.component.html',
  styleUrls: ['./cell.component.css'],
  standalone: false
})
export class GpfTableCellComponent {
  @Input() public columnInfo: GpfTableColumnComponent;
  @Input() public data: any;
  @Input() public noScrollOptimization: boolean;

  public get cellContent(): GpfTableContentComponent {
    return this.columnInfo.contentChildren.first;
  }
}
