import { Pipe, PipeTransform } from '@angular/core';
import { EnrichmentTestResult } from '../enrichment-query/enrichment-result';
import { PValueIntensityPipe } from './p-value-intensity.pipe';

@Pipe({
  name: 'getEnrichmentBackgroundColor',
  standalone: false
})
export class BackgroundColorEnrichmentPipe implements PipeTransform {
  public constructor(private pValueIntensityPipe: PValueIntensityPipe) { }
  public transform(enrichmentResult: EnrichmentTestResult): string {
    const intensity = this.pValueIntensityPipe.transform(enrichmentResult.pvalue) as string;
    if (enrichmentResult.overlapped > enrichmentResult.expected) {
      return `rgba(255, ${intensity}, ${intensity}, 0.60)`;
    } else {
      return `rgba(${intensity}, ${intensity}, 255, 0.4)`;
    }
  }
}
