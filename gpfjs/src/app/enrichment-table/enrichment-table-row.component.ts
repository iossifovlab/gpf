import { Component, Input } from '@angular/core';
import {
  EnrichmentEffectResult, EnrichmentTestResult, GenotypePreviewWithDatasetId
} from '../enrichment-query/enrichment-result';
import { PValueIntensityPipe } from '../utils/p-value-intensity.pipe';
import { QueryService } from '../query/query.service';

@Component({
  selector: '[gpf-enrichment-table-row]',
  templateUrl: './enrichment-table-row.component.html',
  styleUrls: ['./enrichment-table-row.component.css']
})
export class EnrichmentTableRowComponent {
  @Input() label: string;
  @Input() effectResult: EnrichmentEffectResult;

  constructor(
    private pValueIntensityPipe: PValueIntensityPipe,
    private queryService: QueryService
  ) {}

  goToQuery(genotypePreview: GenotypePreviewWithDatasetId) {
    // Create new window now because we are in a 'click' event callback, update
    // it's url later. Otherwise this window.open is treated as a pop-up and
    // being blocked by most browsers.
    // https://stackoverflow.com/a/22470171/2316754
    const newWindow = window.open('', '_blank');
    this.queryService.saveQuery(genotypePreview, 'genotype')
      .take(1)
      .subscribe(urlObject => {
        const url = this.queryService.getLoadUrlFromResponse(urlObject);
        newWindow.location.assign(url);
      });
  }

  getBackgroundColor(testResult: EnrichmentTestResult) {
    const intensity = this.pValueIntensityPipe.transform(testResult.pvalue);

    if (testResult.overlapped > testResult.expected) {
      return `rgba(255, ${intensity}, ${intensity}, 0.8)`;
    } else {
      return `rgba(${intensity}, ${intensity}, 255, 0.8)`;
    }
  }
}
