import { GeneSetsState } from '../gene-sets/gene-sets-state';
import { GeneSymbolsState } from '../gene-symbols/gene-symbols';
import { GeneWeightsState } from '../gene-weights/gene-weights-store';
import { Component, Output, EventEmitter } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryData, Rarity, GeneSetState } from './query';
import { QueryService } from './query.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';
import { PresentInParentState } from '../present-in-parent/present-in-parent';

@Component({
  selector: 'gpf-query-submitter',
  templateUrl: './query-submitter.component.html'
})
export class QuerySubmitterComponent {
  @Output() genotypePreviewsArrayChange = new EventEmitter();

  constructor(
    private store: Store<any>,
    private queryService: QueryService
  ) { }


  submitQuery() {
    this.store.take(1).subscribe(s => this.prepareQuery(s));
  }

  prepareQuery(state: any) {
    console.log('state: ', state);
    let queryData = QueryData.prepare(state);
    console.log('query: ', queryData);

    this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
      (genotypePreviewsArray) => {
        this.genotypePreviewsArrayChange.emit(genotypePreviewsArray);
      });
  }
}
