import { Pipe, PipeTransform } from '@angular/core';
import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

// The comparator is wired into <gpf-table-subheader> via [comparator]
// = "slot.source | compare", and that component's @Input is typed
// over a generic row (object) so it can sort any kind of table data.
// We therefore widen the parameter type to object here and narrow to
// GenotypePreview internally — the pipe is only ever fed
// GenotypePreview rows in practice.
type Comparator = (a: object, b: object) => number;

@Pipe({
  name: 'compare',
  standalone: false
})
export class ComparePipe implements PipeTransform {
  public transform(field: string): Comparator {
    if (field === 'variant.location') {
      return this.locationComparator as Comparator;
    }
    return (a: object, b: object): number => {
      const aPreview = a as GenotypePreview;
      const bPreview = b as GenotypePreview;
      let leftVal: unknown = aPreview.get(field);
      let rightVal: unknown = bPreview.get(field);
      if (leftVal === '-') {
        leftVal = null;
      }
      if (rightVal === '-') {
        rightVal = null;
      }
      if (leftVal === null && rightVal === null) {
        return 0;
      }
      if (leftVal === null) {
        return -1;
      }
      if (rightVal === null) {
        return 1;
      }
      if (Array.isArray(leftVal)) {
        leftVal = (leftVal as unknown[])[0];
      }
      if (Array.isArray(rightVal)) {
        rightVal = (rightVal as unknown[])[0];
      }

      const leftNum = Number(leftVal);
      const rightNum = Number(rightVal);
      if (!isNaN(leftNum) && !isNaN(rightNum)) {
        return leftNum - rightNum;
      }
      const leftStr = typeof leftVal === 'string' ? leftVal : JSON.stringify(leftVal);
      const rightStr = typeof rightVal === 'string' ? rightVal : JSON.stringify(rightVal);
      return leftStr.localeCompare(rightStr);
    };
  }

  public locationComparator(a: GenotypePreview, b: GenotypePreview): number {
    const XYMStringToNum = (str: string): number => {
      if (str === 'X') {
        return 100;
      }
      if (str === 'Y') {
        return 101;
      }
      if (str === 'M') {
        return 102;
      }
      return Number(str);
    };

    const leftRaw = a.get('variant.location');
    const rightRaw = b.get('variant.location');
    const leftVar = typeof leftRaw === 'string' ? leftRaw : '';
    const rightVar = typeof rightRaw === 'string' ? rightRaw : '';

    const leftArr = leftVar.split(':');
    const rightArr = rightVar.split(':');

    if (leftArr[0] === rightArr[0]) {
      return Number(leftArr[1]) - Number(rightArr[1]);
    }
    return XYMStringToNum(leftArr[0]) - XYMStringToNum(rightArr[0]);
  }
}
