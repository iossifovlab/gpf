import { ContentChildren, Component, QueryList } from '@angular/core';
import { GpfTableSubcontentComponent } from './subcontent.component';

@Component({
  selector: 'gpf-table-content',
  template: '',
})
export class GpfTableContentComponent extends GpfTableSubcontentComponent {
  @ContentChildren(GpfTableSubcontentComponent) subcontentChildren: QueryList<GpfTableSubcontentComponent>;
}
