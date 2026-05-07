import { Input, Component, ContentChildren, QueryList, TemplateRef, AfterContentInit } from '@angular/core';
import { GpfTableCellContentDirective } from './content.directive';

@Component({
  selector: 'gpf-table-subcontent',
  template: '',
  standalone: false
})
export class GpfTableSubcontentComponent implements AfterContentInit {
  @ContentChildren(GpfTableCellContentDirective) public contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() public field: string;
  public contentTemplateRef: TemplateRef<unknown>;

  public ngAfterContentInit(): void {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }
}
