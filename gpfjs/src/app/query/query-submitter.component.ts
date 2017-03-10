import { GeneSetsState } from '../gene-sets/gene-sets-state';
import { GeneSymbolsState } from '../gene-symbols/gene-symbols';
import { GeneWeightsState } from '../gene-weights/gene-weights-store';
import { Component, Output, EventEmitter } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryData, Rarity, GeneSetState } from './query';
import { QueryService } from './query.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';
import { PresentInParentState } from '../present-in-parent/present-in-parent';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { toObservableWithValidation } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { GpfState } from "../store/gpf-store";

@Component({
  selector: 'gpf-query-submitter',
  templateUrl: './query-submitter.component.html'
})
export class QuerySubmitterComponent {
  @Output() genotypePreviewsArrayChange = new EventEmitter();

  constructor(
    private store: Store<any>,
    private queryService: QueryService,
    private configService: ConfigService,
    private loadingService: FullscreenLoadingService
  ) { }


  submitQuery() {
    toObservableWithValidation(GpfState, this.store.take(1)).subscribe(([s, valid, errors]) => {
      console.log(errors);
      if (valid) {
        this.prepareQuery(s);
      }
    });
  }

  prepareQuery(state: any) {
    console.log('state: ', state);
    let queryData = QueryData.prepare(state);
    console.log('query: ', queryData);

    this.loadingService.setLoadingStart();
    this.queryService.getGenotypePreviewByFilter(queryData).subscribe(
      (genotypePreviewsArray) => {
        this.loadingService.setLoadingStop();
        this.genotypePreviewsArrayChange.emit(genotypePreviewsArray);
      });
  }


  onSubmit(event) {
    this.store.take(1).subscribe(s => {
      let queryData = QueryData.prepare(s);
      event.target.queryData.value = JSON.stringify(queryData);
      event.target.submit();
    });
  }
}
