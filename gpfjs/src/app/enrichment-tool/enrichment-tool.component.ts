import { Component, OnInit } from '@angular/core';
import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { QueryStateCollector } from '../query/query-state-provider';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css']
})
export class EnrichmentToolComponent extends QueryStateCollector implements OnInit {
  enrichmentResults: EnrichmentResults;
  private selectedDatasetId: string;

  constructor(
    private enrichmentQueryService: EnrichmentQueryService,
    private loadingService: FullscreenLoadingService,
    private route: ActivatedRoute,
  ) {
    super();
  }

  ngOnInit() {
    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
      }
    );
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    let stateArray = this.collectState();
    Observable.zip(...stateArray)
    .subscribe(
      state => {
        this.enrichmentResults = null;
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        this.enrichmentQueryService.getEnrichmentTest(queryData).subscribe(
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
