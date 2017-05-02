import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'pValueIntensity',
  pure: true
})
export class PValueIntensityPipe implements PipeTransform {

  transform(value: any, ...args: any[]): any {
    let number_value = Number(value);
    if(isNaN(number_value)) {
      return '';
    }

    let scale = 0;
    if (number_value >= 0 )  {
      if (number_value >= 0.05 )  {
        scale = 0;
      }
      else {
        if (number_value < 1E-10 )  {
          scale = 10
        }
        else {
          scale = -Math.log10(number_value);
        }
      }
    }

    scale = Math.max(Math.min(scale, 5), 0);
    let intensity = Math.round((5.0 - scale) * 255.0 / 5.0);

    return intensity;
  }
}
