import { Pipe, PipeTransform, inject } from '@angular/core';
import { PValueIntensityPipe } from './p-value-intensity.pipe';

@Pipe({
  name: 'getBackgroundColor',
  standalone: false
})
export class BackgroundColorPipe implements PipeTransform {
  private pValueIntensityPipe = inject(PValueIntensityPipe);

  public transform(pValue: string): string {
    const intensity = this.pValueIntensityPipe.transform(pValue) as number;
    return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
  }
}
