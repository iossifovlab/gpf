import { Component, OnDestroy, OnInit } from '@angular/core';
import { combineLatest, Observable, Subscription, take } from 'rxjs';
import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Store } from '@ngrx/store';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { selectEnrichmentModels } from 'app/enrichment-models/enrichment-models.state';
import { selectGeneScores } from 'app/gene-scores/gene-scores.state';
import { selectGeneSets } from 'app/gene-sets/gene-sets.state';
import { selectGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { selectErrors } from 'app/common/errors_ngrx.state';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css'],
})
export class EnrichmentToolComponent implements OnInit, OnDestroy {
  public enrichmentResults: EnrichmentResults;
  public selectedDatasetId: string;
  public disableQueryButtons = false;

  public enrichmentState: Observable<object[]>;
  private enrichmentToolState = {};
  private enrichmentQuerySubscription: Subscription = null;

  public constructor(
    private enrichmentQueryService: EnrichmentQueryService,
    private loadingService: FullscreenLoadingService,
    private store: Store
  ) { }

  public ngOnInit(): void {
    combineLatest([
      this.store.select(selectGeneSymbols),
      this.store.select(selectGeneSets),
      this.store.select(selectGeneScores),
      this.store.select(selectEnrichmentModels),
      this.store.select(selectDatasetId),
    ]).subscribe(([
      geneSymbols,
      geneSets,
      geneScores,
      enrichmentModels,
      datasetId,
    ]) => {
      this.selectedDatasetId = datasetId;
      this.enrichmentToolState = {
        datasetId: this.selectedDatasetId,
        ...geneSymbols.length && geneSymbols,
        ...geneSets.geneSet && geneSets,
        ...geneScores.geneScores && geneScores,
        ...enrichmentModels,
      };
      this.enrichmentResults = null;
    });

    this.loadingService.interruptEvent.subscribe(() => {
      if (this.enrichmentQuerySubscription !== null) {
        this.enrichmentQuerySubscription.unsubscribe();
        this.enrichmentResults = null;
        this.enrichmentQuerySubscription = null;
        this.loadingService.setLoadingStop();
      }
    });

    this.store.select(selectErrors).subscribe(errorsState => {
      setTimeout(() => {
        this.disableQueryButtons = errorsState.length > 0;
      });
    });
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
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
