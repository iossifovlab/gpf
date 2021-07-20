import { Component, Input, ViewChild } from '@angular/core';
import { Store } from '@ngxs/store';
import { EnrichmentModelsState } from 'app/enrichment-models/enrichment-models.state';
import { StateReset } from 'ngxs-reset-plugin';

@Component({
  selector: 'gpf-enrichment-models-block',
  templateUrl: './enrichment-models-block.component.html',
})
export class EnrichmentModelsBlockComponent {
  @ViewChild('nav') ngbNav;

  @Input()
  private selectedDatasetId: string;

  constructor(private store: Store) { }

  ngAfterViewInit() {
    this.store.selectOnce(EnrichmentModelsState).subscribe(state => {
      if (state.enrichmentBackgroundModel || state.enrichmentCountingModel) {
        setTimeout(() => this.ngbNav.select('models'));
      }
    });
  }

  onNavChange() {
    this.store.dispatch(new StateReset(EnrichmentModelsState));
  }
}
