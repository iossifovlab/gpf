import { Component } from '@angular/core';
import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { QueryStateCollector } from '../query/query-state-provider'
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css']
})
export class EnrichmentToolComponent extends QueryStateCollector {
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
    let state = this.collectState();
    Observable.zip(...state)
    .subscribe(
      state => {
        let queryData = Object.assign({},
                                      {datasetId: this.selectedDatasetId},
                                      ...state);
        console.log("ST", queryData);
        this.enrichmentQueryService.getEnrichmentTest(queryData).subscribe(
          (enrichmentResults) => {
            this.enrichmentResults = enrichmentResults;
            this.loadingService.setLoadingStop();
          });
      },
      error => {
        console.log(error);
        this.loadingService.setLoadingStop();
      }
    )
  }
}
