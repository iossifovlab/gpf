import { Pipe, PipeTransform } from '@angular/core';
import { DecimalPipe } from '@angular/common';

@Pipe({name: 'numberWithExp'})
export class NumberWithExpPipe extends DecimalPipe implements PipeTransform {

  transform(value: any, digits: string = null): string {
    if (typeof value !== 'number') {
      return value;
    }

    if (value >= 0.0001 || value === 0.0) {
      return super.transform(value, digits);
    } else {
      return value.toExponential(1);
    }
  }
}
