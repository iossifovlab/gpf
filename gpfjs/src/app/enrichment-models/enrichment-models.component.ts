import { Component, OnInit, forwardRef } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { EnrichmentModels, EnrichmentModel } from './enrichment-models';
import { IdDescription } from '../common/iddescription';
import { Observable } from 'rxjs';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import {
  toValidationObservable, validationErrorsToStringArray
} from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => EnrichmentModelsComponent) }]
})
export class EnrichmentModelsComponent extends QueryStateWithErrorsProvider implements OnInit {
  enrichmentModels: EnrichmentModels;
  selectedEnrichmentModel = new EnrichmentModel();

  constructor(
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super();
  }

  ngOnInit() {
    this.enrichmentModelsService.getBackgroundModels()
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
