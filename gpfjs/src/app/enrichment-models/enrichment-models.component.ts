import { EnrichmentModelsState, ENRICHMENT_BACKGROUND_CHANGE, ENRICHMENT_COUNTING_CHANGE } from './enrichment-models-state';
import { ENRICHMENT_MODELS_TAB_DESELECT } from '../store/common';
import { Component, OnInit, forwardRef } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { EnrichmentModels } from './enrichment-models';
import { IdDescription } from '../common/iddescription';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider'

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => EnrichmentModelsComponent) }]
})
export class EnrichmentModelsComponent extends QueryStateProvider implements OnInit {
  private enrichmentModels: EnrichmentModels;
  private internalSelectedBackground: IdDescription;
  private internalSelectedCounting: IdDescription;
  private enrichmentModelsState: Observable<EnrichmentModelsState>;

  constructor(
    private store: Store<any>,
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super();
    this.enrichmentModelsState = this.store.select('enrichmentModels');
  }

  ngOnInit() {
    this.enrichmentModelsState.subscribe(
      state => {
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

  onTabChange(event) {
    this.store.dispatch({
      'type': ENRICHMENT_MODELS_TAB_DESELECT,
      'payload': event.activeId
    });
  }

  getState() {
    return this.enrichmentModelsState.take(1).map(
      (enrichmentModels) => {
        // if (!isValid) {
        //   throw "invalid state"
        // }

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
