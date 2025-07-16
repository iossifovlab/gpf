import { ContentChildren, Component, QueryList } from '@angular/core';
import { GpfTableSubcontentComponent } from './subcontent.component';

@Component({
  selector: 'gpf-table-content',
  template: '',
  standalone: false
})
export class GpfTableContentComponent extends GpfTableSubcontentComponent {
  @ContentChildren(GpfTableSubcontentComponent) public subcontentChildren: QueryList<GpfTableSubcontentComponent>;
}
