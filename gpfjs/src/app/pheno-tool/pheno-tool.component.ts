import { Component, OnInit, AfterViewInit } from '@angular/core';
import { DatasetsService } from '../datasets/datasets.service';
import { ActivatedRoute } from '@angular/router';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { FullscreenLoadingService } from '../fullscreen-loading/fullscreen-loading.service';
import { PhenoToolService } from './pheno-tool.service';
import { PhenoToolResults } from './pheno-tool-results';
import { ConfigService } from '../config/config.service';

@Component({
  selector: 'gpf-pheno-tool',

  templateUrl: './pheno-tool.component.html',
  styleUrls: ['./pheno-tool.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: PhenoToolComponent
  }]
})
export class PhenoToolComponent extends QueryStateCollector
    implements OnInit, AfterViewInit {
  selectedDatasetId: string;
  selectedDataset: Dataset;

  phenoToolResults: PhenoToolResults;
  private phenoToolState: Object;

  private disableQueryButtons = false;

  constructor(
    private route: ActivatedRoute,
    private datasetsService: DatasetsService,
    private loadingService: FullscreenLoadingService,
    private phenoToolService: PhenoToolService,
    readonly configService: ConfigService,
  ) {
    super();
  }

  getCurrentState() {
    const state = super.getCurrentState();

    return state.map(state => {
        const stateObject = Object.assign(
          { datasetId: this.selectedDatasetId },
          ...state);
        return stateObject;
      });
  }

  ngAfterViewInit() {
    this.detectNextStateChange(() => {
      this.getCurrentState()
        .subscribe(state => {
          this.phenoToolState = state;
          this.disableQueryButtons = false;
        },
        error => {
          this.disableQueryButtons = true;
          console.warn(error);
        });
    });
  }

  ngOnInit() {
    this.datasetsService.getSelectedDataset()
      .subscribe(dataset => {
        this.selectedDatasetId = dataset.id;
        this.selectedDataset = dataset;
      });
  }

  submitQuery() {
    this.loadingService.setLoadingStart();
    this.getCurrentState().subscribe(
      state => {
        this.phenoToolService.getPhenoToolResults(state).subscribe(
          (phenoToolResults) => {
            this.phenoToolResults = phenoToolResults;
            this.loadingService.setLoadingStop();
          },
          error => {
            this.loadingService.setLoadingStop();
          },
          () => {
            this.loadingService.setLoadingStop();
          });

      },
      error => {
        this.loadingService.setLoadingStop();
      }
    );
  }

  onDownload(event) {
    this.getCurrentState()
      .subscribe(state => {
        event.target.queryData.value = JSON.stringify(state);
        event.target.submit();
      },
      error => null
    );
  }

}
