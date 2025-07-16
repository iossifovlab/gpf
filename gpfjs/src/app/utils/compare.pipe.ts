import { Pipe, PipeTransform } from '@angular/core';
import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

@Pipe({
  name: 'compare',
  standalone: false
})
export class ComparePipe implements PipeTransform {
  public transform(field: string): any {
    if (field === 'variant.location') {
      return this.locationComparator;
    } else {
      return (a: GenotypePreview, b: GenotypePreview) => {
        let leftVal = a.get(field);
        let rightVal = b.get(field);
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
        if (leftVal.constructor === Array) {
          leftVal = leftVal[0];
        }
        if (rightVal.constructor === Array) {
          rightVal = rightVal[0];
        }
        if (!isNaN(leftVal) && !isNaN(rightVal)) {
          return Number(leftVal) - Number(rightVal);
        }
        return leftVal.localeCompare(rightVal);
      };
    }
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

    const leftVar = a.get('variant.location');
    const rightVar = b.get('variant.location');

    const leftArr = leftVar.split(':');
    const rightArr = rightVar.split(':');

    if (leftArr[0] === rightArr[0]) {
      return Number(leftArr[1]) - Number(rightArr[1]);
    } else {
      return XYMStringToNum(leftArr[0]) - XYMStringToNum(rightArr[0]);
    }
  }
}
