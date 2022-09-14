import { Pipe, PipeTransform } from '@angular/core';
@Pipe({name: 'arrayDifference'})
export class ArrayDifferencePipe implements PipeTransform {
  public transform(array1: any[], array2: any[], _: unknown): any[] {
    return array2.filter(element => array1.indexOf(element) === -1);
  }
}
