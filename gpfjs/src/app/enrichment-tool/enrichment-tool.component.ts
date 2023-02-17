import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { Observable, Subscription } from 'rxjs';

import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Select, Selector } from '@ngxs/store';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { EnrichmentModelsState } from 'app/enrichment-models/enrichment-models.state';
import { ErrorsState, ErrorsModel } from 'app/common/errors.state';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css'],
})
export class EnrichmentToolComponent implements OnInit, OnDestroy {
  public enrichmentResults: EnrichmentResults;
  public selectedDataset: Dataset;
  public disableQueryButtons = false;

  @Select(EnrichmentToolComponent.enrichmentToolStateSelector) public state$: Observable<object[]>;
  @Select(ErrorsState) public errorsState$: Observable<ErrorsModel>;
  private enrichmentToolState = {};
  private enrichmentQuerySubscription: Subscription = null;

  public constructor(
    private enrichmentQueryService: EnrichmentQueryService,
    private loadingService: FullscreenLoadingService,
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
  ) { }

  public ngOnInit(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    this.state$.subscribe(state => {
      this.enrichmentToolState = {
        datasetId: this.selectedDataset.id,
        ...state
      };
      this.enrichmentResults = null;
    });

    this.loadingService.interruptEvent.subscribe(_ => {
      if (this.enrichmentQuerySubscription !== null) {
        this.enrichmentQuerySubscription.unsubscribe();
        this.enrichmentResults = null;
        this.enrichmentQuerySubscription = null;
        this.loadingService.setLoadingStop();
      }
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => {
        this.disableQueryButtons = state.componentErrors.size > 0;
      });
    });
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
  }

  @Selector([GenesBlockComponent.genesBlockState, EnrichmentModelsState])
  public static enrichmentToolStateSelector(genesBlockState: object, enrichmentModelsState: object): object {
    return {
      ...genesBlockState, ...enrichmentModelsState,
    };
  }

  public submitQuery(): void {
    this.enrichmentResults = null;
    this.loadingService.setLoadingStart();
    this.enrichmentQuerySubscription =
      this.enrichmentQueryService.getEnrichmentTest(this.enrichmentToolState).subscribe(
        (enrichmentResults) => {
          this.enrichmentResults = enrichmentResults;
          this.loadingService.setLoadingStop();
        },
        () => {
          this.loadingService.setLoadingStop();
        },
        () => {
          this.loadingService.setLoadingStop();
        }
      );
  }
}
