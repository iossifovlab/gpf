import { Input, Component } from '@angular/core';
import { GpfTableColumnComponent } from '../component/column.component';
import { GpfTableContentComponent } from '../component/content.component';
import { SortableTableRow } from '../component/subheader.component';

@Component({
  selector: 'gpf-table-view-cell',
  templateUrl: './cell.component.html',
  styleUrls: ['./cell.component.css'],
  standalone: false
})
export class GpfTableCellComponent {
  @Input() public columnInfo: GpfTableColumnComponent;
  @Input() public data: SortableTableRow;
  @Input() public noScrollOptimization: boolean;

  public get cellContent(): GpfTableContentComponent {
    return this.columnInfo.contentChildren.first;
  }

  /**
   * Fallback rendering for subcontents that declare a `field` but no content
   * template. Rows are arbitrary objects, so the lookup is dynamic.
   */
  public fieldValue(field: string): string {
    const value = (this.data as Record<string, unknown>)[field];
    if (value === null || value === undefined) {
      return null;
    }
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' || typeof value === 'boolean' || typeof value === 'bigint') {
      return value.toString();
    }
    // Non-scalar cell values have no meaningful default rendering; a column
    // that holds one is expected to supply its own content template.
    return JSON.stringify(value);
  }
}
