import { Component, Input, OnInit, OnChanges, SimpleChanges } from '@angular/core';

import { Observable } from 'rxjs';

import { QueryService } from '../query/query.service';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { ConfigService } from '../config/config.service';
import { DatasetsService } from '../datasets/datasets.service';
import { Dataset, SelectorValue } from '../datasets/datasets';
import { GenotypePreviewVariantsArray } from 'app/genotype-preview-model/genotype-preview';
import { Store, Select } from '@ngxs/store';
import { GenotypeBlockState } from '../genotype-block/genotype-block.component';

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

  @Select(GenotypeBlockState.genotypeBlockQueryState) state$: Observable<any[]>;

  constructor(
    private store: Store,
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
      this.genotypeBrowserState = state;
      this.genotypePreviewVariantsArray = null;
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    this.datasetsService.setSelectedDatasetById(this.selectedDatasetId);
  }

  getStateSelector() {
    return GenotypeBlockState.genotypeBlockQueryState;
  }

  submitQuery() {
    this.loadingFinished = false;
    this.loadingService.setLoadingStart();

    this.selectedDataset$.subscribe( selectedDataset => {
      this.genotypePreviewVariantsArray = null;
      this.genotypeBrowserState['datasetId'] = selectedDataset.id;
      this.legend = selectedDataset.peopleGroupConfig.getLegend(this.genotypeBrowserState['peopleGroup']);

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
