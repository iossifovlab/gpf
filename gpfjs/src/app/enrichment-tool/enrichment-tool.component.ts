import { Component, OnInit, AfterViewInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';

import { Observable } from 'rxjs';

import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css'],
})
export class EnrichmentToolComponent implements OnInit, AfterViewInit {
  enrichmentResults: EnrichmentResults;
  public selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;
  private disableQueryButtons = false;

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
  }

  ngAfterViewInit() {
    /* FIXME this.detectNextStateChange(() => {
        this.getCurrentState()
        .take(1)
        .subscribe(
          state => {
            this.disableQueryButtons = false;
          },
          error => {
            this.disableQueryButtons = true;
            console.warn(error);
          });
      });
    */
  }

  getCurrentState() {
    /* FIXME const state = super.getCurrentState();

    return state
      .map(state => {
        const stateObject = Object.assign({ datasetId: this.selectedDatasetId }, state);
        return stateObject;
      });
    */
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    /* FIXME this.getCurrentState().subscribe(
      state => {
        this.enrichmentResults = null;
        this.enrichmentQueryService.getEnrichmentTest(state).subscribe(
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
      },
      error => {
        console.error(error);
        this.loadingService.setLoadingStop();
      }
    ); */
  }
}
