import { Component, Output, EventEmitter } from '@angular/core';
import { Store } from '@ngrx/store';
import { EnrichmentQueryData } from './enrichment-query';
import { EnrichmentQueryService } from './enrichment-query.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';

@Component({
  selector: 'gpf-enrichment-query-submitter',
  templateUrl: './enrichment-query-submitter.component.html'
})
export class EnrichmentQuerySubmitterComponent {
  @Output() genotypePreviewsArrayChange = new EventEmitter();

  constructor(
    private store: Store<any>,
    private queryService: EnrichmentQueryService
  ) { }


  submitQuery() {
    this.store.take(1).subscribe(s => this.prepareQuery(s));
  }

  prepareQuery(state: any) {
    console.log('state: ', state);
    let queryData = EnrichmentQueryData.prepare(state);
    console.log('query: ', queryData);

    this.queryService.getEnrichmentTest(queryData).subscribe(
      (genotypePreviewsArray) => {
        this.genotypePreviewsArrayChange.emit(genotypePreviewsArray);
      });
  }
}
