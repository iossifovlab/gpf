import { Component, Input, forwardRef, OnInit } from '@angular/core';
import { Dataset, MissenseMetric } from '../datasets/datasets';
import { MissenseScoresService } from './genomics-scores.service'
import { MissenseScoresHistogramData } from './genomics-scores';
import { QueryStateProvider } from '../query/query-state-provider'
import { Observable }        from 'rxjs/Observable';
import { ValidationError } from "class-validator";
import { MissenseScoresState, MISSENSE_SCORES_INIT, MISSENSE_SCORES_CHANGE,
         MISSENSE_SCORES_RANGE_START_CHANGE, MISSENSE_SCORES_RANGE_END_CHANGE
 } from './genomics-scores-store';
 import { Store } from '@ngrx/store';
 import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'

@Component({
  selector: 'gpf-missense-scores',
  templateUrl: './genomics-scores.component.html',
  /*providers: [{provide: QueryStateProvider,
               useExisting: forwardRef(() => MissenseScoresComponent) }]*/
})
export class MissenseScoresComponent extends QueryStateProvider {
  @Input() datasetConfig: Dataset;
  @Input() index: number;
  private internalSelectedMetric: MissenseMetric;
  histogramData: MissenseScoresHistogramData;
  private missenseScoresState: Observable<[MissenseScoresState, boolean,
                                           ValidationError[]]>;
  private internalRangeStart = 0;
  private internalRangeEnd = 0;
  errors: string[];

  constructor(
    private store: Store<any>,
    private missenseScoresService: MissenseScoresService
  )  {
    super();
    this.missenseScoresState = toObservableWithValidation(
      MissenseScoresState, this.store.select('missenseScore')
    );
    this.missenseScoresState.subscribe(
      ([missenseScoresState, isValid, validationErrors]) => {
        //this.errors = validationErrorsToStringArray(validationErrors);
        if (this.index < missenseScoresState.missenseScoresState.length) {
            console.log(this.index, missenseScoresState, missenseScoresState.missenseScoresState[this.index])
            this.internalSelectedMetric = missenseScoresState.missenseScoresState[this.index].metric;
            this.histogramData = missenseScoresState.missenseScoresState[this.index].histogramData;
            this.internalRangeStart = missenseScoresState.missenseScoresState[this.index].rangeStart;
            this.internalRangeEnd = missenseScoresState.missenseScoresState[this.index].rangeEnd;
        }
      }
    );
  }

  set selectedMetric(selectedMetric: MissenseMetric) {
    this.missenseScoresService.getHistogramData(this.datasetConfig.id,
        selectedMetric.id).subscribe(
      (histogramData) => {
        this.store.dispatch({
          'type': MISSENSE_SCORES_CHANGE,
          'payload': [this.index, selectedMetric, histogramData, histogramData.min, histogramData.max]
        });
    });
  }

  get selectedMetric() {
    return this.internalSelectedMetric;
  }

  set rangeStart(range: number) {
    this.store.dispatch({
      'type': MISSENSE_SCORES_RANGE_START_CHANGE,
      'payload': range
    });
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  set rangeEnd(range: number) {
    this.store.dispatch({
      'type': MISSENSE_SCORES_RANGE_END_CHANGE,
      'payload': range
    });
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }

  getState() {
    /*return this.missenseScoresState.take(1).map(
      ([missenseScoresState, isValid, validationErrors]) => {
        if (!isValid) {
          //this.flashingAlert = true;
        //  setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid geneWeights state"
        }
        return { missenseScores: {
          metric: missenseScoresState[0].histogramData.metric,
          rangeStart: missenseScoresState[0].rangeStart,
          rangeEnd: missenseScoresState[0].rangeEnd
        }}
    });*/
  }
}
