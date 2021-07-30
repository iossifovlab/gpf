import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';

import { Observable } from 'rxjs';

import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset, SelectorValue } from '../datasets/datasets';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Store, Select, Selector } from '@ngxs/store';
import { GenotypeBlockComponent } from '../genotype-block/genotype-block.component';
import { GenesBlockComponent } from '../genes-block/genes-block.component';
import { RegionsFilterState } from 'app/regions-filter/regions-filter.state';
import { GenomicScoresBlockState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { FamilyFiltersBlockComponent } from 'app/family-filters-block/family-filters-block.component';
import { PersonFiltersBlockComponent } from 'app/person-filters-block/person-filters-block.component';
import { ErrorsState, ErrorsModel } from '../common/errors.state';

@Component({
  selector: 'gpf-genotype-browser',
  templateUrl: './genotype-browser.component.html',
  styleUrls: ['./genotype-browser.component.css'],
})
export class GenotypeBrowserComponent implements OnInit, OnChanges {
  genotypePreviewVariantsArray: GenotypePreviewVariantsArray;
  tablePreview: boolean;
  legend: Array<SelectorValue>;

  private disableQueryButtons = false;

  @Input()
  selectedDatasetId: string;
  selectedDataset$: Observable<Dataset>;
  private genotypeBrowserState: Object;
  private loadingFinished: boolean;

  @Select(GenotypeBrowserComponent.genotypeBrowserStateSelector) state$: Observable<any[]>;
  @Select(ErrorsState) errorsState$: Observable<ErrorsModel>;

  constructor(
    private queryService: QueryService,
    readonly configService: ConfigService,
    private loadingService: FullscreenLoadingService,
    private datasetsService: DatasetsService,
  ) {
  }

  ngOnInit() {
    this.genotypeBrowserState = {};
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();
    this.state$.subscribe(state => {
      this.genotypeBrowserState = {...state};
      this.genotypePreviewVariantsArray = null;
    });

    this.errorsState$.subscribe(state => {
      setTimeout(() => this.disableQueryButtons = state.componentErrors.size > 0);
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    this.datasetsService.setSelectedDatasetById(this.selectedDatasetId);
  }

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

  submitQuery() {
    this.loadingFinished = false;
    this.loadingService.setLoadingStart();

    this.selectedDataset$.subscribe(selectedDataset => {
      this.genotypePreviewVariantsArray = null;
      this.genotypeBrowserState['datasetId'] = selectedDataset.id;
      this.legend = selectedDataset.peopleGroupConfig.getLegend(this.genotypeBrowserState['peopleGroup']);

      /* FIXME: Hack to remove presentInChild and presentInParent from
      query arguments if they are not enabled (would interfere with results).
      This should be removed when a central converter from state to query args
      is implemented. */
      if (!selectedDataset.genotypeBrowserConfig.hasPresentInChild) {
        delete this.genotypeBrowserState['presentInChild'];
      }
      if (!selectedDataset.genotypeBrowserConfig.hasPresentInParent) {
        delete this.genotypeBrowserState['presentInParent'];
      }

      this.queryService.streamingFinishedSubject.subscribe(
        _ => { this.loadingFinished = true; }
      );

      this.genotypePreviewVariantsArray =
        this.queryService.getGenotypePreviewVariantsByFilter(
          this.genotypeBrowserState, selectedDataset.genotypeBrowserConfig.columnIds, this.loadingService
        );

    }, error => {
      console.warn(error);
    });
  }

  onSubmit(event) {
    this.selectedDataset$.subscribe( selectedDataset => {
      const args: any = this.genotypeBrowserState
      this.genotypeBrowserState['datasetId'] = selectedDataset.id;
      args.download = true;
      event.target.queryData.value = JSON.stringify(args);
      event.target.submit();
    }, error => {
        console.warn(error);
    });
  }
}
