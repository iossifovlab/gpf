import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { Observable, Subscription } from 'rxjs';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { Dataset, PersonSet } from '../datasets/datasets';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Select, Selector, Store } from '@ngxs/store';
import { GenotypeBlockComponent } from '../genotype-block/genotype-block.component';
import { GenesBlockComponent } from '../genes-block/genes-block.component';
import { RegionsFilterState } from 'app/regions-filter/regions-filter.state';
import { GenomicScoresBlockState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PersonFiltersBlockComponent } from 'app/person-filters-block/person-filters-block.component';
import { UniqueFamilyVariantsFilterState } from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import { ErrorsState, ErrorsModel } from '../common/errors.state';
import { filter, switchMap, take } from 'rxjs/operators';
import { StudyFiltersState } from 'app/study-filters/study-filters.state';
import { clone } from 'lodash';
import { NavigationStart, Router } from '@angular/router';
import { DatasetModel } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
})
export class GenotypeBrowserComponent implements OnInit, OnDestroy {
  public genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  public showTable = false;
  public legend: Array<PersonSet>;

  public disableQueryButtons = false;
  private routerSubscription: Subscription;

  public selectedDatasetId: string;
  public selectedDataset: Dataset;

  @Input()
  public genotypeBrowserState: object;
  public loadingFinished: boolean;

  public variantsCountDisplay: string;

  @Select(GenotypeBrowserComponent.genotypeBrowserStateSelector) private state$: Observable<any[]>;
  @Select(ErrorsState) private errorsState$: Observable<ErrorsModel>;

  @Selector([
    GenotypeBlockComponent.genotypeBlockQueryState,
    GenesBlockComponent.genesBlockState,
    RegionsFilterState,
    GenomicScoresBlockState,
    FamilyFiltersBlockComponent.familyFiltersBlockState,
    PersonFiltersBlockComponent.personFiltersBlockState,
    UniqueFamilyVariantsFilterState,
    StudyFiltersState
  ])
  public static genotypeBrowserStateSelector(
    genotypeBlockState,
    genesBlockState,
    regionsFilterState,
    genomicScoresBlockState,
    familyFiltersBlockState,
    personFiltersBlockState,
    uniqueFamilyVariantsFilterState,
    StudyFiltersState
  ): object {
    const res = {
      ...genotypeBlockState,
      ...genesBlockState,
      ...genomicScoresBlockState,
      ...familyFiltersBlockState,
      ...personFiltersBlockState,
      ...uniqueFamilyVariantsFilterState,
      ...StudyFiltersState
    };
    if (regionsFilterState.regionsFilters.length) {
      res.regions = regionsFilterState.regionsFilters;
    }
    return res;
  }

  public constructor(
    private queryService: QueryService,
    public readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private router: Router,
    private store: Store,
    private datasetsService: DatasetsService
  ) {
    this.routerSubscription = this.router.events.pipe(
      filter(event => event instanceof NavigationStart)
    ).subscribe(() => {
      this.queryService.cancelStreamPost();
      this.loadingService.setLoadingStop();
    });
  }

  public ngOnInit(): void {
    this.genotypeBrowserState = {};

    this.store.selectOnce((state: { datasetState: DatasetModel}) => state.datasetState).pipe(
      switchMap((state: DatasetModel) => this.datasetsService.getDataset(state.selectedDatasetId))
    ).subscribe(dataset => {
      this.selectedDataset = dataset;
    });

    this.state$.subscribe(state => {
      this.genotypeBrowserState = {...state};
      this.genotypePreviewVariantsArray = null;
    });

    this.loadingService.interruptEvent.subscribe(_ => {
      this.queryService.cancelStreamPost();
      this.loadingService.setLoadingStop();
      this.showTable = false;
      this.loadingFinished = true;
      this.genotypePreviewVariantsArray = null;
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => this.disableQueryButtons = state.componentErrors.size > 0);
    });
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
    this.routerSubscription.unsubscribe();
  }

  public submitQuery(): void {
    this.loadingFinished = false;
    this.showTable = false;
    this.variantsCountDisplay = 'Loading variants...';
    this.loadingService.setLoadingStart();

    this.genotypePreviewVariantsArray = null;
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;
    this.legend = this.selectedDataset.personSetCollections.getLegend(this.genotypeBrowserState['personSetCollection']);

    this.queryService.streamingSubject.pipe(take(1)).subscribe(() => {
      this.showTable = true;
      this.loadingService.setLoadingStop();
    });

    this.queryService.streamingFinishedSubject.pipe(take(1)).subscribe(() => {
      this.showTable = true;
      this.loadingFinished = true;
    });

    this.patchState();
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset,
      this.genotypeBrowserState,
      this.selectedDataset?.genotypeBrowserConfig?.maxVariantsCount !== undefined
        ? this.selectedDataset?.genotypeBrowserConfig?.maxVariantsCount + 1
        : undefined,
      () => {
        this.variantsCountDisplay = this.genotypePreviewVariantsArray?.getVariantsCountFormatted(
          this.selectedDataset?.genotypeBrowserConfig?.maxVariantsCount
        );
      }
    );
  }

  public onSubmit(event): void {
    this.patchState();
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;
    const args = clone(this.genotypeBrowserState);
    args['download'] = true;
    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    event.target.queryData.value = JSON.stringify(args);
    event.target.submit();
    /* eslint-enable */
  }

  private patchState(): void {
    /* FIXME: Hack to remove presentInChild and presentInParent from
      query arguments if they are not enabled (would interfere with results).
      This should be removed when a central converter from state to query args
      is implemented. */
    if (!this.selectedDataset.genotypeBrowserConfig.hasPresentInChild) {
      delete this.genotypeBrowserState['presentInChild'];
    }

    if (!this.selectedDataset.genotypeBrowserConfig.hasPresentInParent) {
      delete this.genotypeBrowserState['presentInParent'];
    }
  }
}
