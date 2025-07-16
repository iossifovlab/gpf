import { Component, Input } from '@angular/core';
import { EnrichmentResults } from '../enrichment-query/enrichment-result';

@Component({
    selector: 'gpf-enrichment-table',
    templateUrl: './enrichment-table.component.html',
    styleUrls: ['./enrichment-table.component.css'],
    standalone: false
})
export class EnrichmentTableComponent {
  @Input() public enrichmentResults: EnrichmentResults;
}
