import { Component, Input, Directive } from '@angular/core';
import { EnrichmentResults, EnrichmentEffectResult } from '../enrichment-query/enrichment-result';



@Component({
  selector: 'gpf-enrichment-table',
  templateUrl: './enrichment-table.component.html',
  styleUrls: ['./enrichment-table.component.css']
})
export class EnrichmentTableComponent {
  @Input() enrichmentResults: EnrichmentResults;
}
