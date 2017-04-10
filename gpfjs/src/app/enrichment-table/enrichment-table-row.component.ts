import { Component, Input, Directive } from '@angular/core';
import {
  EnrichmentResults, EnrichmentEffectResult, EnrichmentTestResult
} from '../enrichment-query/enrichment-result';

@Component({
  selector: '[gpf-enrichment-table-row]',
  templateUrl: './enrichment-table-row.component.html',
  styleUrls: ['./enrichment-table-row.component.css']
})
export class EnrichmentTableRowComponent {
  @Input() label: string;
  @Input() effectResult: EnrichmentEffectResult;

  getBackgroundColor(testResult: EnrichmentTestResult) {
    let scale = 0;
    if (testResult.pvalue >= 0 )  {
      if (testResult.pvalue >= 0.05 )  {
        scale = 0;
      }
      else {
        if (testResult.pvalue < 1E-10 )  {
          scale = 10
        }
        else {
          scale = -Math.log10(testResult.pvalue);
        }
      }
    }

    scale = Math.max(Math.min(scale, 5), 0);
    let intensity = Math.round((5.0 - scale) * 255.0 / 5.0);

    if (testResult.overlapped > testResult.expected) {
      return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
    }
    else {
      return `rgba(${intensity}, ${intensity}, 255, 0.8)`;
    }
  }
}
