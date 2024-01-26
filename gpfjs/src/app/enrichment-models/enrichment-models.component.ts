import { Component, OnInit, Input } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { IdDescriptionName } from './iddescription';
import { Subscription, combineLatest, of } from 'rxjs';
import { Allow } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetEnrichmentModels, EnrichmentModelsState, EnrichmentModelsModel } from './enrichment-models.state';
import { switchMap, take } from 'rxjs/operators';
import { StatefulComponent } from 'app/common/stateful-component';
import { environment } from 'environments/environment';
import { FullscreenLoadingService } from 'app/fullscreen-loading/fullscreen-loading.service';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
})
export class EnrichmentModelsComponent extends StatefulComponent implements OnInit {
  @Input() private selectedDatasetId: string;
  private modelsSubscription: Subscription = null;

  @Allow() public background: IdDescriptionName;
  @Allow() public counting: IdDescriptionName;

  public countings: Array<IdDescriptionName>;
  public backgrounds: Array<IdDescriptionName>;

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store,
    private enrichmentModelsService: EnrichmentModelsService,
    private loadingService: FullscreenLoadingService
  ) {
    super(store, EnrichmentModelsState, 'enrichmentModels');
  }

  public ngOnInit(): void {
    this.loadingService.setLoadingStart();

    this.loadingService.interruptEvent.subscribe(() => {
      if (this.modelsSubscription !== null) {
        this.modelsSubscription.unsubscribe();
        this.modelsSubscription = null;
        this.loadingService.setLoadingStop();
      }
    });

    super.ngOnInit();
    this.modelsSubscription = this.enrichmentModelsService.getBackgroundModels(this.selectedDatasetId).pipe(
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
        this.background = res.backgrounds.find(bg => bg.id === res.defaultBackground);
        this.counting = res.countings.find(ct => ct.id === res.defaultCounting);
      }
      this.loadingService.setLoadingStop();
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
