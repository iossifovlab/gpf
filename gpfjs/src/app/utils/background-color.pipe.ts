import { Pipe, PipeTransform } from '@angular/core';
import { PValueIntensityPipe } from './p-value-intensity.pipe';

@Pipe({
    name: 'getBackgroundColor',
    standalone: false
})
export class BackgroundColorPipe implements PipeTransform {
  public constructor(private pValueIntensityPipe: PValueIntensityPipe) {}
  public transform(pValue: string): string {
    const intensity = this.pValueIntensityPipe.transform(pValue) as number;
    return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
  }
}
