import { Input, Component, ContentChildren, QueryList, TemplateRef } from '@angular/core';
import { GpfTableCellContentDirective } from './content.directive';

@Component({
  selector: 'gpf-table-subheader',
  template: '',
})
export class GpfTableSubheaderComponent {
  @ContentChildren(GpfTableCellContentDirective) contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() field: string;
  @Input() caption: string;
  @Input() comparator: (leftVal: any, rightVal: any) => number = this.defaultComparator;

  contentTemplateRef: TemplateRef<any>;

  get sortable () {
      return this.field || this.comparator != this.defaultComparator;
  }

  ngAfterContentInit() {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }

  defaultComparator(a: any, b: any): number {
    let leftVal = a[this.field];
    let rightVal = b[this.field];

    if (leftVal == null && rightVal == null) { return 0; }
    if (leftVal == null) { return -1; }
    if (rightVal == null) { return 1; }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }

  sort(data: any, ascending: boolean) {
    data.sort((a, b) => {
      if (ascending) {
        return this.comparator(a, b);
      } else {
        return this.comparator(b, a);
      }
    });
  }
}
