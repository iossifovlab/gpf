import { Component, Output, EventEmitter } from '@angular/core';
import { Store } from '@ngrx/store';
import { EnrichmentQueryData } from './enrichment-query';
import { EnrichmentQueryService } from './enrichment-query.service';

@Component({
  selector: 'gpf-enrichment-query-submitter',
  templateUrl: './enrichment-query-submitter.component.html'
})
export class EnrichmentQuerySubmitterComponent {
  @Output() enrichmentResultsChange = new EventEmitter();

  constructor(
    private store: Store<any>,
    private enrichmentQueryService: EnrichmentQueryService
  ) { }


  submitQuery() {
    this.store.take(1).subscribe(s => this.prepareQuery(s));
  }

  prepareQuery(state: any) {
    console.log('state: ', state);
    let queryData = EnrichmentQueryData.prepare(state);
    console.log('query: ', queryData);

    this.enrichmentQueryService.getEnrichmentTest(queryData).subscribe(
      (enrichmentResults) => {
        this.enrichmentResultsChange.emit(enrichmentResults);
      });
  }
}
