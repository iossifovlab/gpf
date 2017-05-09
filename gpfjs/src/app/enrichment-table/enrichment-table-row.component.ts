import { Component, Input, Directive } from '@angular/core';
import {
  EnrichmentResults, EnrichmentEffectResult, EnrichmentTestResult,
  GenotypePreviewWithDatasetId
} from '../enrichment-query/enrichment-result';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';

@Component({
  selector: '[gpf-enrichment-table-row]',
  templateUrl: './enrichment-table-row.component.html',
  styleUrls: ['./enrichment-table-row.component.css']
})
export class EnrichmentTableRowComponent {
  @Input() label: string;
  @Input() effectResult: EnrichmentEffectResult;
  withoutDatasetId = GenotypePreviewWithDatasetId.withoutDatasetId;

  getStateObject(genotypePreview: GenotypePreviewWithDatasetId): object {
    return {
      state: this.toJson(GenotypePreviewWithDatasetId.withoutDatasetId(genotypePreview))
    };
  }

  toJson(obj: any): string {
    return JSON.stringify(obj);
  };

  constructor(
    private pValueIntensityPipe: PValueIntensityPipe
  ) {}

  getBackgroundColor(testResult: EnrichmentTestResult) {
    let intensity = this.pValueIntensityPipe.transform(testResult.pvalue);

    if (testResult.overlapped > testResult.expected) {
      return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
    } else {
      return `rgba(${intensity}, ${intensity}, 255, 0.8)`;
    }
  }
}
