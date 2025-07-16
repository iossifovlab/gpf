import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'getRows',
  standalone: false
})
export class GetVariantReportRowsPipe implements PipeTransform {
  public transform(effectGroups: string[], effectTypes: string[]): string[] {
    let result: string[] = [];

    if (effectGroups) {
      result = effectGroups.concat(effectTypes);
    } else if (effectTypes) {
      result = effectTypes;
    }

    return result;
  }
}
