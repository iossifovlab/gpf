import { Input, ContentChildren, QueryList, Component } from '@angular/core';
import { GpfTableContentHeaderComponent } from './header.component';
import { GpfTableContentComponent } from './content.component';

@Component({
  selector: 'gpf-table-column',
  template: '',
})
export class GpfTableColumnComponent {
  @ContentChildren(GpfTableContentHeaderComponent) public headerChildren: QueryList<GpfTableContentHeaderComponent>;
  @ContentChildren(GpfTableContentComponent) public contentChildren: QueryList<GpfTableContentComponent>;
  @Input() public columnWidth = '';
  @Input() public columnMaxWidth = '';
}
