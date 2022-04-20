import { AfterViewInit, Component, Input, ViewChild } from '@angular/core';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngxs/store';
import { EnrichmentModelsModel, EnrichmentModelsState } from 'app/enrichment-models/enrichment-models.state';
import { StateReset } from 'ngxs-reset-plugin';

@Component({
  selector: 'gpf-enrichment-models-block',
  templateUrl: './enrichment-models-block.component.html',
})
export class EnrichmentModelsBlockComponent implements AfterViewInit {
  @ViewChild('nav') public ngbNav: NgbNav;

  @Input()
  public selectedDatasetId: string;

  public constructor(private store: Store) { }

  public ngAfterViewInit(): void {
    this.store.selectOnce(EnrichmentModelsState).subscribe(state => {
      const enrichmentModelsState = state as EnrichmentModelsModel;
      if (enrichmentModelsState.enrichmentBackgroundModel || enrichmentModelsState.enrichmentCountingModel) {
        setTimeout(() => this.ngbNav.select('models'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new StateReset(EnrichmentModelsState));
  }
}
