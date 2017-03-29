import { Component, Input, Directive } from '@angular/core';
import { EnrichmentResults, EnrichmentEffectResult } from '../enrichment-query/enrichment-result';

@Component({
  selector: '[gpf-enrichment-table-row]',
  styleUrls: ['./enrichment-table.component.css'],
  template: `
    <td>{{ label }}</td>
    <td>{{ effectResult.all.count | number: "1.0-2"  }}</td>
    <td>{{ effectResult.all.overlapped | number: "1.0-2"  }}</td>
    <td>{{ effectResult.all.expected | number: "1.2-2" }}</td>
    <td>{{ effectResult.all.pvalue | number: "1.2-4"  }}</td>
    <td>{{ effectResult.rec.count | number: "1.0-2"  }}</td>
    <td>{{ effectResult.rec.overlapped | number: "1.0-2" }}</td>
    <td>{{ effectResult.rec.expected  | number: "1.2-2"}}</td>
    <td>{{ effectResult.rec.pvalue | number: "1.2-4"}}</td>
    <td>{{ effectResult.male.count | number: "1.0-2"  }}</td>
    <td>{{ effectResult.male.overlapped | number: "1.0-2" }}</td>
    <td>{{ effectResult.male.expected | number: "1.2-2" }}</td>
    <td>{{ effectResult.male.pvalue | number: "1.2-4"}}</td>
    <td>{{ effectResult.female.count | number: "1.0-2"  }}</td>
    <td>{{ effectResult.female.overlapped | number: "1.0-2" }}</td>
    <td>{{ effectResult.female.expected  | number: "1.2-2"}}</td>
    <td>{{ effectResult.female.pvalue | number: "1.2-4"}}</td>
  `
})
export class EnrichmentTableRowComponent {
  @Input() label: string;
  @Input() effectResult: EnrichmentEffectResult;
}


@Component({
  selector: 'gpf-enrichment-table',
  templateUrl: './enrichment-table.component.html',
  styleUrls: ['./enrichment-table.component.css']
})
export class EnrichmentTableComponent {
  @Input() enrichmentResults: EnrichmentResults;

  ngOnChanges(changes: any) {
    console.log(this.enrichmentResults)
  }
}
