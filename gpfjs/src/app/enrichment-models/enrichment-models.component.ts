import { Component, OnInit, Input } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { IdDescription } from '../common/iddescription';
import { combineLatest, of } from 'rxjs';
import { IsNotEmpty } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetEnrichmentModels, EnrichmentModelsState } from './enrichment-models.state';
import { switchMap } from 'rxjs/operators';
import { StatefulComponent } from 'app/common/stateful-component';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
})
export class EnrichmentModelsComponent extends StatefulComponent implements OnInit {

  @Input()
  private selectedDatasetId: string;

  @IsNotEmpty()
  background: IdDescription;

  @IsNotEmpty()
  counting: IdDescription;

  countings: Array<IdDescription>
  backgrounds: Array<IdDescription>

  constructor(
    protected store: Store,
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super(store, EnrichmentModelsState, 'enrichmentModels');
  }

  ngOnInit() {
    super.ngOnInit();
    this.enrichmentModelsService.getBackgroundModels(this.selectedDatasetId)
      .take(1).pipe(
        switchMap(res => {
          return combineLatest(
            of(res), this.store.selectOnce(EnrichmentModelsState)
          );
        })
      ).subscribe(([res, state]) => {
        this.backgrounds = res.backgrounds;
        this.countings = res.countings;
        if (state.enrichmentBackgroundModel || state.enrichmentCountingModel) {
          this.background = res.backgrounds.find(bg => bg.id === state.enrichmentBackgroundModel);
          this.counting = res.countings.find(ct => ct.id === state.enrichmentCountingModel);
        } else {
          this.background = res.backgrounds[0];
          this.counting = res.countings[0];
          this.store.dispatch(new SetEnrichmentModels(this.background.id, this.counting.id));
        }
    });
  }

  changeBackground(newValue: IdDescription) {
    this.background = newValue;
    this.store.dispatch(new SetEnrichmentModels(this.background.id, this.counting.id));
  }

  changeCounting(newValue: IdDescription) {
    this.counting = newValue;
    this.store.dispatch(new SetEnrichmentModels(this.background.id, this.counting.id));
  }
}
