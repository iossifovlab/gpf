import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { PhenoToolService } from './pheno-tool.service';
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';
import { Observable, Subscription, switchMap } from 'rxjs';
import { GenesBlockComponent } from 'app/genes-block/genes-block.component';
import { PhenoToolGenotypeBlockComponent } from 'app/pheno-tool-genotype-block/pheno-tool-genotype-block.component';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PhenoToolMeasureState } from 'app/pheno-tool-measure/pheno-tool-measure.state';
import { Select, Selector, Store } from '@ngxs/store';
import { ErrorsState, ErrorsModel } from 'app/common/errors.state';
import {
  PHENO_TOOL_CNV, PHENO_TOOL_LGDS, PHENO_TOOL_OTHERS
} from 'app/pheno-tool-effect-types/pheno-tool-effect-types';
import { DatasetModel } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-pheno-tool',
  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css'],
})
export class PhenoToolComponent implements OnInit, OnDestroy {
  @Select(PhenoToolComponent.phenoToolStateSelector) public state$: Observable<object[]>;
  @Select(ErrorsState) public errorsState$: Observable<ErrorsModel>;

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

  @Selector([
    GenesBlockComponent.genesBlockState,
    PhenoToolMeasureState,
    PhenoToolGenotypeBlockComponent.phenoToolGenotypeBlockQueryState,
    FamilyFiltersBlockComponent.familyFiltersBlockState,
  ])
  public static phenoToolStateSelector(
    genesBlockState: object, measureState: object, genotypeState: object, familyFiltersState: object
  ): object {
    return {
      ...genesBlockState,
      ...measureState,
      ...genotypeState,
      ...familyFiltersState,
    };
  }

  public ngOnInit(): void {
    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap((state: DatasetModel) => this.datasetsService.getDataset(state.selectedDatasetId))
    ).subscribe(dataset => {
      if (!dataset) {
        return;
      }
      this.selectedDataset = dataset;
      this.variantTypesSet = new Set(this.selectedDataset.genotypeBrowserConfig.variantTypes);
    });

    this.state$.subscribe(state => {
      this.phenoToolState = state;
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

    this.errorsState$.subscribe(state => {
      setTimeout(() => {
        this.disableQueryButtons = state.componentErrors.size > 0;
      });
    });
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
