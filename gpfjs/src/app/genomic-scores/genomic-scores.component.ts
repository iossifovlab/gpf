import { Component, Input, forwardRef, OnInit } from '@angular/core';
import { Dataset, GenomicMetric } from '../datasets/datasets';
import { GenomicScoresService } from './genomic-scores.service';
import { GenomicScoresHistogramData } from './genomic-scores';
import { Observable }        from 'rxjs/Observable';
import { ValidationError } from 'class-validator';
import { GenomicScoreState } from './genomic-scores-store';
 import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
 import { transformAndValidate } from 'class-transformer-validator';
 import { StateRestoreService } from '../store/state-restore.service';
 import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
})
export class GenomicScoresComponent implements OnInit {
  @Input() index: number;
  @Input() genomicScoreState: GenomicScoreState;

  errors: string[];
  private dataset: Dataset;

  constructor(
    private genomicsScoresService: GenomicScoresService,
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService
  ) {
  }


  set selectedMetric(selectedMetric: GenomicMetric) {
    this.genomicsScoresService
      .getHistogramData(this.dataset.id, selectedMetric.id)
      .take(1)
      .subscribe((histogramData) => {
        let state = this.genomicScoreState;
        if (state) {
          state.metric = selectedMetric;
          state.histogramData = histogramData;
          state.rangeStart = null;
          state.rangeEnd = null;
          state.domainMin = histogramData.bins[0];
          state.domainMax = histogramData.bins[histogramData.bins.length - 1];
        }
    });
  }

  get selectedMetric() {
    return this.genomicScoreState.metric;
  }

  set rangeStart(range: number) {
    this.genomicScoreState.rangeStart = range;
  }

  get rangeStart() {
    return this.genomicScoreState.rangeStart;
  }

  set rangeEnd(range: number) {
    this.genomicScoreState.rangeEnd = range;
  }

  get rangeEnd() {
    return this.genomicScoreState.rangeEnd;
  }

    ngOnInit() {
        this.datasetsService.getSelectedDataset().subscribe(dataset => {
          this.dataset = dataset;
          this.stateRestoreService
            .getState(this.constructor.name + this.index)
            .subscribe(state => {
                if (!state['genomicScores'] || this.index < state['genomicScores'].length) {
                    return;
                }
                let score = state['genomicScores'][this.index];
                let metric = this.dataset.genotypeBrowser.genomicMetrics
                    .find(m => m.id === score.metric);
                if (!metric) {
                    return;
                }
                this.selectedMetric = metric;
                this.rangeStart = score.rangeStart;
                this.rangeEnd = score.rangeEnd;
            });
        });
  }
}
