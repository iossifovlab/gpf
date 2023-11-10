import { Component, OnInit, Input } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { IdDescriptionName } from './iddescription';
import { combineLatest, of } from 'rxjs';
import { Allow } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetEnrichmentModels, EnrichmentModelsState, EnrichmentModelsModel } from './enrichment-models.state';
import { switchMap, take } from 'rxjs/operators';
import { StatefulComponent } from 'app/common/stateful-component';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
})
export class EnrichmentModelsComponent extends StatefulComponent implements OnInit {
  @Input() private selectedDatasetId: string;

  @Allow() public background: IdDescriptionName;
  @Allow() public counting: IdDescriptionName;

  public countings: Array<IdDescriptionName>;
  public backgrounds: Array<IdDescriptionName>;

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store,
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super(store, EnrichmentModelsState, 'enrichmentModels');
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.enrichmentModelsService.getBackgroundModels(this.selectedDatasetId).pipe(
      take(1),
      switchMap(res => combineLatest([of(res), this.store.selectOnce(EnrichmentModelsState)]))
    ).subscribe(([res, enrichmentState]) => {
      this.backgrounds = res.backgrounds;
      this.countings = res.countings;
      const state = enrichmentState as EnrichmentModelsModel;
      if (state.enrichmentBackgroundModel || state.enrichmentCountingModel) {
        this.background = res.backgrounds.find(bg => bg.id === state.enrichmentBackgroundModel);
        this.counting = res.countings.find(ct => ct.id === state.enrichmentCountingModel);
      } else {
        this.background = res.backgrounds[0];
        this.counting = res.countings[0];
      }
      this.store.dispatch(new SetEnrichmentModels(this.background.id, this.counting.id));
    });
  }

  public changeBackground(newValue: IdDescriptionName): void {
    this.background = newValue;
    this.store.dispatch(new SetEnrichmentModels(this.background.id, this.counting.id));
  }

  public changeCounting(newValue: IdDescriptionName): void {
    this.counting = newValue;
    this.store.dispatch(new SetEnrichmentModels(this.background.id, this.counting.id));
  }
}
