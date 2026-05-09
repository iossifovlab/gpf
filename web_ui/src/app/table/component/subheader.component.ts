import { Input, Component, ContentChildren, QueryList, TemplateRef, AfterContentInit } from '@angular/core';
import { GpfTableCellContentDirective } from './content.directive';

// Rows can be any object shape; the subheader narrows to a dynamic
// dictionary internally for the default field-based comparator.
type SortableTableRow = object & { arrayPosition?: number };

@Component({
  selector: 'gpf-table-subheader',
  template: '',
  standalone: false
})
export class GpfTableSubheaderComponent implements AfterContentInit {
  @ContentChildren(GpfTableCellContentDirective) public contentChildren: QueryList<GpfTableCellContentDirective>;
  @Input() public field: string;
  @Input() public caption: string;
  @Input() public comparator: (leftVal: object, rightVal: object) => number = this.defaultComparator;

  public contentTemplateRef: TemplateRef<unknown>;

  public get sortable(): string | boolean {
    return this.field || this.comparator !== this.defaultComparator;
  }

  public ngAfterContentInit(): void {
    if (this.contentChildren.first) {
      this.contentTemplateRef = this.contentChildren.first.templateRef;
    }
  }

  public defaultComparator(a: object, b: object): number {
    let leftVal: unknown = (a as Record<string, unknown>)[this.field];
    let rightVal: unknown = (b as Record<string, unknown>)[this.field];

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

    const leftNum = Number(leftVal);
    const rightNum = Number(rightVal);
    if (!isNaN(leftNum) && !isNaN(rightNum)) {
      return leftNum - rightNum;
    }
    const leftStr = typeof leftVal === 'string' ? leftVal : JSON.stringify(leftVal);
    const rightStr = typeof rightVal === 'string' ? rightVal : JSON.stringify(rightVal);
    return leftStr.localeCompare(rightStr);
  }

  public sort(data: SortableTableRow[], ascending: boolean): void {
    data.forEach((element, idx) => {
      element.arrayPosition = idx;
    });
    data.sort((a, b) => {
      const compareResult = ascending ? this.comparator(a, b) : this.comparator(b, a);
      if (compareResult === 0) {
        return (a.arrayPosition ?? 0) - (b.arrayPosition ?? 0);
      }
      return compareResult;
    });
  }
}
