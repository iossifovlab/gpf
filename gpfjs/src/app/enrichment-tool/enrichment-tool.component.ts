import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';

import { Observable } from 'rxjs';

import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { QueryStateCollector } from '../query/query-state-provider';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: EnrichmentToolComponent
  }]
})
export class EnrichmentToolComponent extends QueryStateCollector implements OnInit {
  enrichmentResults: EnrichmentResults;
  public selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;

  constructor(
    private enrichmentQueryService: EnrichmentQueryService,
    private loadingService: FullscreenLoadingService,
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
  ) {
    super();
  }

  ngOnInit() {
    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
      }
    );
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
  }

  getCurrentState() {
    const state = super.getCurrentState();

    return state
      .map(state => {
        const stateObject = Object.assign(
          { datasetId: this.selectedDatasetId },
          ...state);
        return stateObject;
      });
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    this.getCurrentState().subscribe(
      state => {
        this.enrichmentResults = null;
        this.enrichmentQueryService.getEnrichmentTest(state).subscribe(
          (enrichmentResults) => {
            this.enrichmentResults = enrichmentResults;
            this.loadingService.setLoadingStop();
          },
          error => {
            this.loadingService.setLoadingStop();
          },
          () => {
            this.loadingService.setLoadingStop();
          });
      },
      error => {
        this.loadingService.setLoadingStop();
      }
    );
  }
}
