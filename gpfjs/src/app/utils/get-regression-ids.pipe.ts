import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'getRegressionIds'
})
export class GetRegressionIdsPipe implements PipeTransform {
  public transform(regressionNames): string[] {
    return Object.getOwnPropertyNames(regressionNames);
  }
}
