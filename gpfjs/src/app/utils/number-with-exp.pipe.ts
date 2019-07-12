import { Pipe, PipeTransform } from '@angular/core';
import { DecimalPipe } from '@angular/common';

@Pipe({name: 'numberWithExp'})
export class NumberWithExpPipe extends DecimalPipe implements PipeTransform {

  transform(value: any, digits: string = null): string {
    if (typeof value !== 'number') {
      return value;
    }

    let digitArgs = digits.split('.');
    let minIntegerDigits = +digitArgs[0] || 1;
    digitArgs = digitArgs[1].split('-');
    let minFractionDigits = +digitArgs[0] || 0;
    let maxFractionDigits = +digitArgs[1] || 3;

    if (value >= Math.pow(10, -maxFractionDigits) || value === 0.0) {
      return super.transform(value, digits);
    } else {
      return value.toExponential(minFractionDigits);
    }
  }
}
