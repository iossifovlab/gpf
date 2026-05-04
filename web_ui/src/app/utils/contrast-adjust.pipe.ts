import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'contrastAdjust',
  standalone: false
})
export class ContrastAdjustPipe implements PipeTransform {
  public transform(rgba: string): string {
    const res = rgba.match(/\d{1,3}, \d{1,3}, \d{1,3}, \d*/).toString().split(',');
    if ((Number(res[0]) <= 75 || Number(res[0]) >= 230) && (Number(res[1]) <= 75)) {
      return '#00209f';
    } else {
      return '#0000EE';
    }
  }
}
