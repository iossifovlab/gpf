import { GpfTableSubheaderComponent } from './subheader.component';

class DefaultComparator {
  constructor(private subcolumn: GpfTableSubheaderComponent) {
  }

  compare(a: any, b: any): Number {
    let leftVal = a[this.subcolumn.field];
    let rightVal = b[this.subcolumn.field];

    if (leftVal == null && rightVal == null) { return 0; }
    if (leftVal == null) { return -1; }
    if (rightVal == null) { return 1; }

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }
}
