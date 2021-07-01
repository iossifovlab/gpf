import { Component, OnInit, Input, OnDestroy } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { IdDescription } from '../common/iddescription';
import { Observable, Subscription } from 'rxjs';
import { IsNotEmpty, validate } from 'class-validator';
import { Store, Select } from '@ngxs/store';
import { SetEnrichmentModels, EnrichmentModelsModel, EnrichmentModelsState } from './enrichment-models.state';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
})
export class EnrichmentModelsComponent implements OnInit {

  @Input()
  private selectedDatasetId: string;

  @IsNotEmpty()
  background: IdDescription;

  @IsNotEmpty()
  counting: IdDescription;

  countings: Array<IdDescription>
  backgrounds: Array<IdDescription>

  stateSubscription: Subscription;
  @Select(EnrichmentModelsState) state$: Observable<EnrichmentModelsModel>;
  errors: Array<string> = [];

  constructor(
    private store: Store,
    private enrichmentModelsService: EnrichmentModelsService,
  ) { }

  ngOnInit() {
    this.store.selectOnce(state => state.enrichmentModelsState).subscribe(state => {
      // restore state
      this.background = state.enrichmentBackgroundModel;
      this.counting = state.enrichmentCountingModel;
    });

    this.stateSubscription = this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });

    this.enrichmentModelsService.getBackgroundModels(this.selectedDatasetId)
      .take(1)
      .subscribe(res => {
        this.backgrounds = res.backgrounds;
        this.countings = res.countings;
        this.background = res.backgrounds[0];
        this.counting = res.countings[0];
        this.store.dispatch(new SetEnrichmentModels(this.background, this.counting));
      });
  }

  ngOnDestroy() {
    this.stateSubscription.unsubscribe();
  }

  changeBackground(newValue: IdDescription) {
    this.background = newValue;
    this.store.dispatch(new SetEnrichmentModels(this.background, this.counting));
  }

  changeCounting(newValue: IdDescription) {
    this.counting = newValue;
    this.store.dispatch(new SetEnrichmentModels(this.background, this.counting));
  }
}
