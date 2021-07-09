import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';

import { Observable } from 'rxjs';

import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Select, Selector } from '@ngxs/store';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { EnrichmentModelsState } from 'app/enrichment-models/enrichment-models.state';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css'],
})
export class EnrichmentToolComponent implements OnInit {
  enrichmentResults: EnrichmentResults;
  public selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;
  private disableQueryButtons = false;

  @Select(EnrichmentToolComponent.enrichmentToolStateSelector) state$: Observable<any[]>;
  private enrichmentToolState = {};

  constructor(
    private enrichmentQueryService: EnrichmentQueryService,
    private loadingService: FullscreenLoadingService,
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit() {
    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params['dataset'];
      }
    );
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();

    this.state$.subscribe(state => {
      this.enrichmentToolState = {
        'datasetId': this.selectedDatasetId,
        ...state
      };
      this.enrichmentResults = null;
    });
  }

  @Selector([GenesBlockComponent.genesBlockState, EnrichmentModelsState])
  static enrichmentToolStateSelector(genesBlockState, enrichmentModelsState) {
    return {
      ...genesBlockState, ...enrichmentModelsState,
    };
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    this.enrichmentQueryService.getEnrichmentTest(this.enrichmentToolState).subscribe(
      (enrichmentResults) => {
        this.enrichmentResults = enrichmentResults;
        this.loadingService.setLoadingStop();
      },
      error => {
        console.error(error);
        this.loadingService.setLoadingStop();
      },
      () => {
        this.loadingService.setLoadingStop();
    });
  }
}
