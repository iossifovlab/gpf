import { Component, Input, forwardRef, OnInit } from '@angular/core';
import { Dataset, GenomicMetric } from '../datasets/datasets';
import { GenomicScoresService } from './genomic-scores.service'
import { GenomicScoresHistogramData } from './genomic-scores';
import { Observable }        from 'rxjs/Observable';
import { ValidationError } from "class-validator";
import { GenomicScoresState, GENOMIC_SCORES_INIT, GENOMIC_SCORES_CHANGE,
         GENOMIC_SCORES_RANGE_START_CHANGE, GENOMIC_SCORES_RANGE_END_CHANGE
 } from './genomic-scores-store';
 import { Store } from '@ngrx/store';
 import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'

@Component({
  selector: 'gpf-genomic-scores',
  templateUrl: './genomic-scores.component.html',
})
export class GenomicScoresComponent {
  @Input() datasetConfig: Dataset;
  @Input() index: number;
  private internalSelectedMetric: GenomicMetric;
  histogramData: GenomicScoresHistogramData;
  private genomicScoresState: Observable<[GenomicScoresState, boolean,
                                           ValidationError[]]>;
  private internalRangeStart = 0;
  private internalRangeEnd = 0;
  errors: string[];

  constructor(
    private store: Store<any>,
    private genomicsScoresService: GenomicScoresService
  )  {
    this.genomicScoresState = toObservableWithValidation(
      GenomicScoresState, this.store.select('genomicScores')
    );
    this.genomicScoresState.subscribe(
      ([genomicScoresState, isValid, validationErrors]) => {
        //this.errors = validationErrorsToStringArray(validationErrors);
        if (this.index < genomicScoresState.genomicScoresState.length) {
            console.log(this.index, genomicScoresState, genomicScoresState.genomicScoresState[this.index])
            this.internalSelectedMetric = genomicScoresState.genomicScoresState[this.index].metric;
            this.histogramData = genomicScoresState.genomicScoresState[this.index].histogramData;
            this.internalRangeStart = genomicScoresState.genomicScoresState[this.index].rangeStart;
            this.internalRangeEnd = genomicScoresState.genomicScoresState[this.index].rangeEnd;
        }
      }
    );
  }

  set selectedMetric(selectedMetric: GenomicMetric) {
    this.genomicsScoresService.getHistogramData(this.datasetConfig.id,
        selectedMetric.id).subscribe(
      (histogramData) => {
        this.store.dispatch({
          'type': GENOMIC_SCORES_CHANGE,
          'payload': [this.index, selectedMetric, histogramData, histogramData.min, histogramData.max]
        });
    });
  }

  get selectedMetric() {
    return this.internalSelectedMetric;
  }

  set rangeStart(range: number) {
    this.store.dispatch({
      'type': GENOMIC_SCORES_RANGE_START_CHANGE,
      'payload': [this.index, range]
    });
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  set rangeEnd(range: number) {
    this.store.dispatch({
      'type': GENOMIC_SCORES_RANGE_END_CHANGE,
      'payload': [this.index, range]
    });
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }

}
