import { EnrichmentModelsState, ENRICHMENT_BACKGROUND_CHANGE, ENRICHMENT_COUNTING_CHANGE } from './enrichment-models-state';
import { ENRICHMENT_MODELS_TAB_DESELECT } from '../store/common';
import { Component, OnInit } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { EnrichmentModels } from './enrichment-models';
import { IdDescription } from '../common/iddescription';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
})
export class EnrichmentModelsComponent implements OnInit {
  private enrichmentModels: EnrichmentModels;
  private internalSelectedBackground: IdDescription;
  private internalSelectedCounting: IdDescription;
  private enrichmentModelsState: Observable<EnrichmentModelsState>;

  constructor(
    private store: Store<any>,
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
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
}
