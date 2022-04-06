import { Component, Input, OnInit } from '@angular/core';

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
import { ErrorsState, ErrorsModel } from '../common/errors.state';
import { clone } from 'lodash';
import { take } from 'rxjs/operators';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
})
export class GenotypeBrowserComponent implements OnInit {
  genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  tablePreview: boolean;
  legend: Array<PersonSet>;

  public disableQueryButtons = false;

  @Input()
  selectedDatasetId: string;
  selectedDataset: Dataset;
  public genotypeBrowserState: Object;
  public loadingFinished: boolean;

  @Select(GenotypeBrowserComponent.genotypeBrowserStateSelector) state$: Observable<any[]>;
  @Select(ErrorsState) errorsState$: Observable<ErrorsModel>;

  @Selector([
    GenotypeBlockComponent.genotypeBlockQueryState,
    GenesBlockComponent.genesBlockState,
    RegionsFilterState,
    GenomicScoresBlockState,
    FamilyFiltersBlockComponent.familyFiltersBlockState,
    PersonFiltersBlockComponent.personFiltersBlockState,
  ])
  static genotypeBrowserStateSelector(
    genotypeBlockState,
    genesBlockState,
    regionsFilterState,
    genomicScoresBlockState,
    familyFiltersBlockState,
    personFiltersBlockState,
  ) {
    const res = {
      ...genotypeBlockState,
      ...genesBlockState,
      ...genomicScoresBlockState,
      ...familyFiltersBlockState,
      ...personFiltersBlockState,
    };
    if (regionsFilterState['regionsFilters'].length) {
      res['regions'] = regionsFilterState['regionsFilters'];
    }
    return res;
  }

  constructor(
    private queryService: QueryService,
    readonly configService: ConfigService,
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

    this.queryService.streamingSubject.pipe(take(1)).subscribe(() => {
      this.loadingFinished = true;
      this.loadingService.setLoadingStop();
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => this.disableQueryButtons = state.componentErrors.size > 0);
    });
  }

  public submitQuery(): void {
    this.loadingFinished = false;
    this.loadingService.setLoadingStart();

    this.genotypePreviewVariantsArray = null;
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;
    this.legend = this.selectedDataset.personSetCollections.getLegend(this.genotypeBrowserState['personSetCollection']);

    this.patchState();
    this.genotypePreviewVariantsArray = this.queryService.getGenotypePreviewVariantsByFilter(
      this.selectedDataset, this.genotypeBrowserState
    );
  }

  public onSubmit(event): void {
    this.patchState();
    this.genotypeBrowserState['datasetId'] = this.selectedDataset.id;

    const args = clone(this.genotypeBrowserState);
    args['download'] = true;

    event.target.queryData.value = JSON.stringify(args);
    event.target.submit();
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
