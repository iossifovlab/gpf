import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset, PersonSet } from '../datasets/datasets';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Select, Selector } from '@ngxs/store';
import { GenotypeBlockComponent } from '../genotype-block/genotype-block.component';
import { GenesBlockComponent } from '../genes-block/genes-block.component';
import { RegionsFilterState } from 'app/regions-filter/regions-filter.state';
import { GenomicScoresBlockState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PersonFiltersBlockComponent } from 'app/person-filters-block/person-filters-block.component';
import { UniqueFamilyVariantsFilterState } from 'app/unique-family-variants-filter/unique-family-variants-filter.state';
import { ErrorsState, ErrorsModel } from '../common/errors.state';
import { take } from 'rxjs/operators';
import { StudyFiltersBlockState } from 'app/study-filters-block/study-filters-block.state';
import { downloadBlobResponse } from 'app/utils/blob-download';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
})
export class GenotypeBrowserComponent implements OnInit, OnDestroy {
  public genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  public tablePreview: boolean;
  public legend: Array<PersonSet>;

  public disableQueryButtons = false;

  @Input()
  public selectedDatasetId: string;
  public selectedDataset: Dataset;
  public genotypeBrowserState: object;
  public loadingFinished: boolean;

  public downloadInProgress = false;

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
    StudyFiltersBlockState
  ])
  public static genotypeBrowserStateSelector(
    genotypeBlockState,
    genesBlockState,
    regionsFilterState,
    genomicScoresBlockState,
    familyFiltersBlockState,
    personFiltersBlockState,
    uniqueFamilyVariantsFilterState,
    StudyFiltersBlockState
  ): object {
    const res = {
      ...genotypeBlockState,
      ...genesBlockState,
      ...genomicScoresBlockState,
      ...familyFiltersBlockState,
      ...personFiltersBlockState,
      ...uniqueFamilyVariantsFilterState,
      ...StudyFiltersBlockState
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
    private datasetsService: DatasetsService,
  ) { }

  public ngOnInit(): void {
    this.genotypeBrowserState = {};

    this.selectedDataset = this.datasetsService.getSelectedDataset();

    this.state$.subscribe(state => {
      this.genotypeBrowserState = {...state};
      this.genotypePreviewVariantsArray = null;
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => this.disableQueryButtons = state.componentErrors.size > 0);
    });
  }

  public ngOnDestroy(): void {
    this.loadingService.setLoadingStop();
  }

  public submitQuery(): void {
    this.loadingFinished = false;
    this.loadingService.setLoadingStart();

    this.genotypePreviewVariantsArray = null;
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;
    this.legend = this.selectedDataset.personSetCollections.getLegend(this.genotypeBrowserState['personSetCollection']);

    this.queryService.streamingSubject.pipe(take(1)).subscribe(() => {
      this.loadingService.setLoadingStop();
    });

    this.queryService.streamingFinishedSubject.pipe(take(1)).subscribe(() => {
      this.loadingFinished = true;
    });

    this.patchState();
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset, this.genotypeBrowserState
    );
  }

  public onDownload(): void {
    this.downloadInProgress = true;
    this.patchState();

    const args = {
      ...this.genotypeBrowserState,
      datasetId: this.selectedDataset.id,
      download: true
    };

    this.queryService.downloadVariants(args).pipe(take(1)).subscribe((response) => {
      this.downloadInProgress = false;
      downloadBlobResponse(response, 'variants.tsv');
    }, (err) => {
      this.downloadInProgress = false;
    });
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
