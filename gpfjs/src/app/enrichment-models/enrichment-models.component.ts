import { Component, OnInit, forwardRef } from '@angular/core';
import { EnrichmentModelsService } from './enrichment-models.service';
import { EnrichmentModels, EnrichmentModel } from './enrichment-models';
import { IdDescription } from '../common/iddescription';
import { Observable } from 'rxjs';
import { QueryStateProvider } from '../query/query-state-provider';
import {
  toValidationObservable, validationErrorsToStringArray
} from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';

@Component({
  selector: 'gpf-enrichment-models',
  templateUrl: './enrichment-models.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => EnrichmentModelsComponent) }]
})
export class EnrichmentModelsComponent extends QueryStateProvider implements OnInit {
  enrichmentModels: EnrichmentModels;
  selectedEnrichmentModel = new EnrichmentModel();

  errors: string[];
  flashingAlert = false;

  constructor(
    private enrichmentModelsService: EnrichmentModelsService,
  ) {
    super();
  }

  ngOnInit() {
    this.enrichmentModelsService.getBackgroundModels().subscribe(
      (res) => {
        this.enrichmentModels = res;

        this.selectedEnrichmentModel.background = res.backgrounds[0];
        this.selectedEnrichmentModel.counting = res.countings[0];
      });
  }

  getState() {
    return toValidationObservable(this.selectedEnrichmentModel)
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
      })
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);

        return Observable.throw(
          `${this.constructor.name}: invalid enrichment models state`);
      });
  }
}
