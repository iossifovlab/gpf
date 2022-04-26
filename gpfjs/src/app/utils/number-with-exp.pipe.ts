import { Pipe, PipeTransform } from '@angular/core';
import { DecimalPipe } from '@angular/common';

@Pipe({name: 'numberWithExp'})
export class NumberWithExpPipe extends DecimalPipe implements PipeTransform {
  public transform(value: string | number, digits?: string): null;
  public transform(value: string | number, digits?: string): string {
    if (typeof value !== 'number') {
      return value;
    }

    let digitArgs = digits.split('.');
    digitArgs = digitArgs[1].split('-');
    const minFractionDigits = Number(digitArgs[0]) || 0;
    const maxFractionDigits = Number(digitArgs[1]) || 3;

    if (value >= Math.pow(10, -maxFractionDigits) || value === 0.0) {
      return super.transform(value, digits);
    } else {
      return value.toExponential(minFractionDigits);
    }
  }
}
