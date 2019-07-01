import { Component, OnInit, forwardRef, Input } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { EnrichmentModels, EnrichmentModel } from './enrichment-models';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => EnrichmentModelsComponent) }]
})
export class EnrichmentModelsComponent extends QueryStateWithErrorsProvider implements OnInit {
  @Input()
  private selectedDatasetId: string;

  enrichmentModels: EnrichmentModels;
  selectedEnrichmentModel = new EnrichmentModel();

  constructor(
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super();
  }

  ngOnInit() {
    this.enrichmentModelsService.getBackgroundModels(this.selectedDatasetId)
      .take(1)
      .subscribe(res => {
        this.enrichmentModels = res;

        this.selectedEnrichmentModel.background = res.backgrounds[0];
        this.selectedEnrichmentModel.counting = res.countings[0];
      });
  }

  getState() {
    return this.validateAndGetState(this.selectedEnrichmentModel)
      .map(enrichmentModel => {
        let enrichmentBackgroundModel = null;
        let enrichmentCountingModel = null;

        if (enrichmentModel && enrichmentModel.background) {
          enrichmentBackgroundModel = enrichmentModel.background.id;
        }

        if (enrichmentModel && enrichmentModel.counting) {
          enrichmentCountingModel = enrichmentModel.counting.id;
        }

        return {
          enrichmentBackgroundModel: enrichmentBackgroundModel,
          enrichmentCountingModel: enrichmentCountingModel,
        };
      });
  }
}
