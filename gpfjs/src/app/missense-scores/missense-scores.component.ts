import { Component, Input, forwardRef, OnInit } from '@angular/core';
import { Dataset, MissenseMetric } from '../datasets/datasets';
import { MissenseScoresService } from './missense-scores.service'
import { MissenseScoresHistogramData } from './missense-scores';
import { QueryStateProvider } from '../query/query-state-provider'
import { Observable }        from 'rxjs/Observable';
import { ValidationError } from "class-validator";
import { MissenseScoresState, MISSENSE_SCORES_INIT, MISSENSE_SCORES_CHANGE,
         MISSENSE_SCORES_RANGE_START_CHANGE, MISSENSE_SCORES_RANGE_END_CHANGE
 } from './missense-scores-store';
 import { Store } from '@ngrx/store';
 import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'

@Component({
  selector: 'gpf-missense-scores',
  templateUrl: './missense-scores.component.html',
  providers: [{provide: QueryStateProvider,
               useExisting: forwardRef(() => MissenseScoresComponent) }]
})
export class MissenseScoresComponent extends QueryStateProvider implements OnInit {
  @Input() datasetConfig: Dataset;
  private internalSelectedMetric: MissenseMetric;
  private histogramData: MissenseScoresHistogramData;
  private missenseScoresState: Observable<[MissenseScoresState, boolean,
                                           ValidationError[]]>;

  private internalRangeStart = 0;
  private internalRangeEnd = 0;

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

        this.histogramData = missenseScoresState.histogramData;
        this.internalRangeStart = missenseScoresState.rangeStart;
        this.internalRangeEnd = missenseScoresState.rangeEnd;
      }
    );
  }

  ngOnInit() {
    this.store.dispatch({
      'type': MISSENSE_SCORES_INIT,
    });
  }

  set selectedMetric(selectedMetric: MissenseMetric) {
    this.internalSelectedMetric = selectedMetric;
    this.missenseScoresService.getHistogramData(this.datasetConfig.id,
        selectedMetric.id).subscribe(
      (histogramData) => {
        this.store.dispatch({
          'type': MISSENSE_SCORES_CHANGE,
          'payload': [histogramData, histogramData.min, histogramData.max]
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
    return this.missenseScoresState.take(1).map(
      ([missenseScoresState, isValid, validationErrors]) => {
        if (!isValid) {
          //this.flashingAlert = true;
        //  setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid geneWeights state"
        }
        return { missenseScores: {
          metric: missenseScoresState.histogramData.metric,
          rangeStart: missenseScoresState.rangeStart,
          rangeEnd: missenseScoresState.rangeEnd
        }}
    });
  }
}
