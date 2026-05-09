import { Pipe, PipeTransform } from '@angular/core';

interface RegressionRow {
  regressions: Record<string, Record<string, unknown> | null>;
}

@Pipe({
  name: 'regressionComparePipe',
  standalone: false
})
export class RegressionComparePipe implements PipeTransform {
  public transform(regressionId: string, field: string):
    (a: RegressionRow, b: RegressionRow) => number {
    return (a, b): number => {
      const leftRegression = a.regressions[regressionId];
      const rightRegression = b.regressions[regressionId];

      const leftVal: number | null = !leftRegression || isNaN(Number(leftRegression[field]))
        ? null : Number(leftRegression[field]);
      const rightVal: number | null = !rightRegression || isNaN(Number(rightRegression[field]))
        ? null : Number(rightRegression[field]);

      if (leftVal === null && rightVal === null) {
        return 0;
      }
      if (leftVal === null) {
        return -1;
      }
      if (rightVal === null) {
        return 1;
      }
      return leftVal - rightVal;
    };
  }
}
