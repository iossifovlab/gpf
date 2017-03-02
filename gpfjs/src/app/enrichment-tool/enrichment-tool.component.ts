import { Component } from '@angular/core';
import { EnrichmentResults } from '../enrichment-query/enrichment-result';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
})
export class EnrichmentToolComponent {
  private enrichmentResults: EnrichmentResults;
}
