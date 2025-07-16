import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
    name: 'regressionComparePipe',
    standalone: false
})
export class RegressionComparePipe implements PipeTransform {
  public transform(regressionId: string, field: string) {
    return (a: any, b: any) => {
      let leftVal = a['regressions'][regressionId];
      let rightVal = b['regressions'][regressionId];

      leftVal = !leftVal || isNaN(leftVal[field]) ? null : leftVal[field];
      rightVal = !rightVal || isNaN(rightVal[field]) ? null : rightVal[field];

      if (leftVal === null && rightVal === null) {
        return 0;
      }
      if (leftVal === null) {
        return -1;
      }
      if (rightVal === null) {
        return 1;
      }
      return Number(leftVal) - Number(rightVal);
    };
  }
}
