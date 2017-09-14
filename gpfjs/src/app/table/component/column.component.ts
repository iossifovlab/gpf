import { ContentChildren, ViewContainerRef, QueryList, ViewChildren, Component } from '@angular/core';

import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableCellContentComponent } from './cell.component';

@Component({
  selector: 'gpf-table-column',
  template: '',
})
export class GpfTableColumnComponent {
  @ContentChildren(GpfTableContentHeaderComponent) headerChildren: QueryList<GpfTableContentHeaderComponent>;
  @ContentChildren(GpfTableCellContentComponent) cellContentChildren: QueryList<GpfTableCellContentComponent>;
  public width = 0;

  constructor(viewContainer: ViewContainerRef) {
  }
}
