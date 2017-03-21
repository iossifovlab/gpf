import { EnrichmentModelsState, ENRICHMENT_BACKGROUND_CHANGE, ENRICHMENT_COUNTING_CHANGE,
         ENRICHMENT_MODELS_INIT } from './enrichment-models-state';
import { Component, OnInit, forwardRef } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { EnrichmentModels } from './enrichment-models';
import { IdDescription } from '../common/iddescription';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => EnrichmentModelsComponent) }]
})
export class EnrichmentModelsComponent extends QueryStateProvider implements OnInit {
  private enrichmentModels: EnrichmentModels;
  private internalSelectedBackground: IdDescription;
  private internalSelectedCounting: IdDescription;
  private enrichmentModelsState: Observable<[EnrichmentModelsState, boolean, ValidationError[]]>;

  private errors: string[];
  private flashingAlert = false;

  constructor(
    private store: Store<any>,
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super();
    this.enrichmentModelsState = toObservableWithValidation(EnrichmentModelsState, this.store.select('enrichmentModels'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': ENRICHMENT_MODELS_INIT,
    });


    this.enrichmentModelsState.subscribe(
      ([state, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

        this.internalSelectedBackground = state.background;
        this.internalSelectedCounting = state.counting;
      }
    );

    this.enrichmentModelsService.getBackgroundModels().subscribe(
      (res) => {
        this.enrichmentModels = res;
      });
  }

  set selectedBackground(background: IdDescription) {
    this.store.dispatch({
      'type': ENRICHMENT_BACKGROUND_CHANGE,
      'payload': background
    });
  }

  get selectedBackground() {
    return this.internalSelectedBackground;
  }

  set selectedCounting(counting: IdDescription) {
    this.store.dispatch({
      'type': ENRICHMENT_COUNTING_CHANGE,
      'payload': counting
    });
  }

  get selectedCounting() {
    return this.internalSelectedCounting;
  }

  getState() {
    return this.enrichmentModelsState.take(1).map(
      ([enrichmentModels, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid enrichment models state"
        }

        let enrichmentBackgroundModel = null;
        let enrichmentCountingModel = null

        if (enrichmentModels && enrichmentModels.background) {
          enrichmentBackgroundModel = enrichmentModels.background.id
        }

        if (enrichmentModels && enrichmentModels.counting) {
          enrichmentCountingModel = enrichmentModels.counting.id
        }


        return {
          enrichmentBackgroundModel: enrichmentBackgroundModel,
          enrichmentCountingModel: enrichmentCountingModel
         }
    });
  }
}
