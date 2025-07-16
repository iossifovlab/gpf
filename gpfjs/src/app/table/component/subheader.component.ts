import { Input, Component, ContentChildren, QueryList, TemplateRef, AfterContentInit } from '@angular/core';
import { GpfTableCellContentDirective } from './content.directive';

@Component({
  selector: 'gpf-table-subheader',
  template: '',
  standalone: false
})
export class GpfTableSubheaderComponent implements AfterContentInit {
  @ContentChildren(GpfTableCellContentDirective) public contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() public field: string;
  @Input() public caption: string;
  @Input() public comparator: (leftVal: any, rightVal: any) => number = this.defaultComparator;

  public contentTemplateRef: TemplateRef<any>;

  public get sortable(): string | boolean {
    return this.field || this.comparator !== this.defaultComparator;
  }

  public ngAfterContentInit(): void {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }

  public defaultComparator(a: any, b: any): number {
    let leftVal = a[this.field];
    let rightVal = b[this.field];

    if (leftVal === '-') {
      leftVal = null;
    }
    if (rightVal === '-') {
      rightVal = null;
    }
    if ((leftVal === undefined || leftVal === null) && (rightVal === undefined || rightVal === null)) {
      return 0;
    }
    if (leftVal === undefined || leftVal === null) {
      return -1;
    }
    if (rightVal === undefined || rightVal === null) {
      return 1;
    }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return Number(leftVal) - Number(rightVal);
    }
    return leftVal.localeCompare(rightVal);
  }

  public sort(data: any, ascending: boolean) {
    data.forEach((element, idx) => {
      element.arrayPosition = idx;
    });
    data.sort((a, b) => {
      const compareResult = ascending ? this.comparator(a, b) : this.comparator(b, a);
      if (compareResult === 0) {
        return a.arrayPosition - b.arrayPosition;
      }
      return compareResult;
    });
  }
}
