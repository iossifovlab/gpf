import { Component, OnDestroy, OnInit } from '@angular/core';
import { combineLatest, Observable, of, Subscription, switchMap } from 'rxjs';
import { EnrichmentResults } from '../enrichment-query/enrichment-result';
import { EnrichmentQueryService } from '../enrichment-query/enrichment-query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { Store } from '@ngrx/store';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { selectEnrichmentModels } from 'app/enrichment-models/enrichment-models.state';
import { selectGeneScores } from 'app/gene-scores/gene-scores.state';
import { selectGeneSets } from 'app/gene-sets/gene-sets.state';
import { selectGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { selectErrors } from 'app/common/errors.state';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Dataset } from 'app/datasets/datasets';

@Component({
  selector: 'gpf-enrichment-tool',
  templateUrl: './enrichment-tool.component.html',
  styleUrls: ['./enrichment-tool.component.css'],
})
export class EnrichmentToolComponent implements OnInit, OnDestroy {
  public enrichmentResults: EnrichmentResults;
  public selectedDataset: Dataset;
  public disableQueryButtons = false;

  public enrichmentState: Observable<object[]>;
  public enrichmentQuerySubscription: Subscription = null;
  private enrichmentToolState = {};

  public constructor(
    private enrichmentQueryService: EnrichmentQueryService,
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private store: Store
  ) { }

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(
      switchMap(selectedDatasetidState => this.datasetsService.getDataset(
        selectedDatasetidState
      )),
      switchMap(dataset => combineLatest([
        of(dataset),
        this.store.select(selectGeneSymbols),
        this.store.select(selectGeneSets),
        this.store.select(selectGeneScores),
        this.store.select(selectEnrichmentModels),
      ]))
    ).subscribe(([
      dataset,
      geneSymbols,
      geneSets,
      geneScores,
      enrichmentModels,
    ]) => {
      this.selectedDataset = dataset;
      this.enrichmentToolState = {
        datasetId: this.selectedDataset.id,
        ...enrichmentModels,
      };
      if (geneSymbols.length) {
        this.enrichmentToolState['geneSymbols'] = geneSymbols;
      } else if (geneSets.geneSet) {
        this.enrichmentToolState['geneSet'] = {
          geneSet: geneSets.geneSet.name,
          geneSetsCollection: geneSets.geneSetsCollection.name,
          geneSetsTypes: geneSets.geneSetsTypes
        };
      } else if (geneScores.score) {
        this.enrichmentToolState['geneScores'] = geneScores;
      }
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
