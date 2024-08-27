import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { PhenoToolService } from './pheno-tool.service';
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';
import { combineLatest, Observable, Subscription, switchMap, take } from 'rxjs';
import { selectPhenoToolMeasure } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { Store } from '@ngrx/store';
import { ErrorsState, ErrorsModel } from 'app/common/errors.state';
import {
  PHENO_TOOL_CNV, PHENO_TOOL_LGDS, PHENO_TOOL_OTHERS
} from 'app/pheno-tool-effect-types/pheno-tool-effect-types';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';
import { selectGeneScores } from 'app/gene-scores/gene-scores.state';
import { selectGeneSets } from 'app/gene-sets/gene-sets.state';
import { selectGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { selectPresentInParent } from 'app/present-in-parent/present-in-parent.state';
import { selectEffectTypes } from 'app/effect-types/effect-types.state';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css'],
})
export class PhenoToolComponent implements OnInit, OnDestroy {
  // @Select(ErrorsState) public errorsState$: Observable<ErrorsModel>;

  public selectedDataset: Dataset;
  public variantTypesSet: Set<string>;

  public phenoToolResults: PhenoToolResults;
  public phenoToolState: object;

  public disableQueryButtons = false;

  private phenoToolSubscription: Subscription = null;

  public constructor(
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService,
    public readonly configService: ConfigService,
    private store: Store,
    private datasetsService: DatasetsService
  ) { }


  @HostListener('keydown', ['$event'])
  public onKeyDown($event: KeyboardEvent): void {
    if ($event.ctrlKey && $event.code === 'Enter') {
      this.submitQuery();
    }
  }

  public ngOnInit(): void {
    this.store.select(selectDatasetId).pipe(
      take(1),
      switchMap(datasetId => this.datasetsService.getDataset(datasetId))
    ).subscribe(dataset => {
      if (!dataset) {
        return;
      }
      this.selectedDataset = dataset;
      this.variantTypesSet = new Set(this.selectedDataset.genotypeBrowserConfig.variantTypes);
    });

    combineLatest([
      this.store.select(selectGeneSymbols),
      this.store.select(selectGeneSets),
      this.store.select(selectGeneScores),
      this.store.select(selectPhenoToolMeasure),
      this.store.select(selectEffectTypes),
      this.store.select(selectPresentInParent),
    ]).subscribe(([
      geneSymbolsState,
      geneSetsState,
      geneScoresState,
      phenoToolMeasureState,
      effectTypesState,
      presentInParentState,
    ]) => {
      const presentInParentRarity = {
        presentInParent: presentInParentState.presentInParent
      };
      if (presentInParentState.presentInParent.length === 1 && presentInParentState.presentInParent[0] === 'neither') {
        return presentInParentRarity;
      }
      presentInParentRarity['rarity'] = { ultraRare: presentInParentState.rarityType === 'ultraRare' };
      if (presentInParentState.rarityType !== 'ultraRare' && presentInParentState.rarityType !== 'all') {
        presentInParentRarity['rarity']['minFreq'] = presentInParentState.rarityIntervalStart;
        presentInParentRarity['rarity']['maxFreq'] = presentInParentState.rarityIntervalEnd;
      }

      this.phenoToolState = {
        ...geneSymbolsState,
        ...geneSetsState,
        ...geneScoresState,
        ...phenoToolMeasureState,
        ...effectTypesState,
        ...presentInParentRarity,
      };
      this.phenoToolResults = null;
    });

    this.loadingService.interruptEvent.subscribe(_ => {
      if (this.phenoToolSubscription !== null) {
        this.phenoToolSubscription.unsubscribe();
        this.phenoToolSubscription = null;
      }
      this.loadingService.setLoadingStop();
      this.phenoToolResults = null;
    });

    // this.errorsState$.subscribe(state => {
    //   setTimeout(() => {
    //     this.disableQueryButtons = state.componentErrors.size > 0;
    //   });
    // });
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
  }

  public submitQuery(): void {
    this.phenoToolResults = null;
    this.loadingService.setLoadingStart();
    this.phenoToolSubscription = this.phenoToolService.getPhenoToolResults(
      {datasetId: this.selectedDataset.id, ...this.phenoToolState}
    ).subscribe((phenoToolResults) => {
      this.phenoToolResults = phenoToolResults;

      const columnSortOrder = [
        ...PHENO_TOOL_LGDS, ...PHENO_TOOL_OTHERS, ...PHENO_TOOL_CNV
      ].map(effect => effect.toLowerCase());
      this.phenoToolResults.results.sort((a, b) =>
        columnSortOrder.indexOf(a.effect.toLowerCase()) - columnSortOrder.indexOf(b.effect.toLowerCase())
      );

      this.loadingService.setLoadingStop();
    }, () => {
      this.loadingService.setLoadingStop();
    }, () => {
      this.loadingService.setLoadingStop();
    });
  }

  public onDownload(event: Event): void {
    if (event.target instanceof HTMLFormElement) {
      event.target.queryData.value = JSON.stringify({...this.phenoToolState, datasetId: this.selectedDataset.id});
      event.target.submit();
    }
  }
}
