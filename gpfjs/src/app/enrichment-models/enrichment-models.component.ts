import { Component, OnInit, Input } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { IdDescriptionName } from './iddescription';
import { combineLatest, of } from 'rxjs';
import { Allow } from 'class-validator';
import { Store } from '@ngrx/store';
import { switchMap, take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { selectEnrichmentModels, setEnrichmentModels } from './enrichment-models.state';
import { ComponentValidator } from 'app/common/component-validator';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
})
export class EnrichmentModelsComponent extends ComponentValidator implements OnInit {
  @Input() private selectedDatasetId: string;

  @Allow() public background: IdDescriptionName;
  @Allow() public counting: IdDescriptionName;

  public countings: Array<IdDescriptionName>;
  public backgrounds: Array<IdDescriptionName>;
  public modelsLoaded = false;

  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
    protected store: Store,
    private enrichmentModelsService: EnrichmentModelsService
  ) {
    super(store, 'enrichmentModels', selectEnrichmentModels);
  }

  public ngOnInit(): void {
    super.ngOnInit();
    this.enrichmentModelsService.getBackgroundModels(this.selectedDatasetId).pipe(
      take(1),
      switchMap(res => combineLatest([of(res), this.store.select(selectEnrichmentModels)])),
      take(1)
    ).subscribe(([res, enrichmentModels]) => {
      this.backgrounds = res.backgrounds;
      this.countings = res.countings;
      if (enrichmentModels.enrichmentBackgroundModel || enrichmentModels.enrichmentCountingModel) {
        this.background = res.backgrounds.find(bg => bg.id === enrichmentModels.enrichmentBackgroundModel);
        this.counting = res.countings.find(ct => ct.id === enrichmentModels.enrichmentCountingModel);
      } else {
        this.background = res.backgrounds.find(bg => bg.id === res.defaultBackground);
        this.counting = res.countings.find(ct => ct.id === res.defaultCounting);
      }
      this.modelsLoaded = true;
      this.store.dispatch(setEnrichmentModels({
        enrichmentBackgroundModel: this.background.id,
        enrichmentCountingModel: this.counting.id
      }));
    });
  }

  public changeBackground(newValue: IdDescriptionName): void {
    this.background = newValue;
    this.store.dispatch(setEnrichmentModels({
      enrichmentBackgroundModel: this.background.id,
      enrichmentCountingModel: this.counting.id
    }));
  }

  public changeCounting(newValue: IdDescriptionName): void {
    this.counting = newValue;
    this.store.dispatch(setEnrichmentModels({
      enrichmentBackgroundModel: this.background.id,
      enrichmentCountingModel: this.counting.id
    }));
  }
}
