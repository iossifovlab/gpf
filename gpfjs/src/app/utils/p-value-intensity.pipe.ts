import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'pValueIntensity',
  pure: true,
  standalone: false
})
export class PValueIntensityPipe implements PipeTransform {
  public transform(value: any, ...args: any[]): any {
    const numberValue = Number(value);
    if (isNaN(numberValue)) {
      return '';
    }

    let scale = 0;
    if (numberValue >= 0) {
      if (numberValue >= 0.05) {
        scale = 0;
      } else if (numberValue < 1E-10) {
        scale = 10;
      } else {
        scale = -Math.log10(numberValue);
      }
    }

    scale = Math.max(Math.min(scale, 5), 0);
    const intensity = Math.round((5.0 - scale) * 255.0 / 5.0);

    return intensity;
  }
}
