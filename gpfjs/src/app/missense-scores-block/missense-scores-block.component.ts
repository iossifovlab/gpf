import { Component, Input, forwardRef } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';
import { environment } from '../../environments/environment';

import { Observable }        from 'rxjs/Observable';
import { ValidationError } from "class-validator";
import { MissenseScoresState, MISSENSE_SCORES_INIT, MISSENSE_SCORES_CHANGE,
         MISSENSE_SCORES_RANGE_START_CHANGE, MISSENSE_SCORES_RANGE_END_CHANGE,
         MISSENSE_SCORE_ADD, MISSENSE_SCORE_REMOVE
 } from '../missense-scores/missense-scores-store';
 import { Store } from '@ngrx/store';
 import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'


@Component({
  selector: 'gpf-missense-scores-block',
  templateUrl: './missense-scores-block.component.html',
  styleUrls: ['./missense-scores-block.component.css'],
  providers: [{provide: QueryStateCollector,
               useExisting: forwardRef(() => MissenseScoresBlockComponent) }]
})
export class MissenseScoresBlockComponent extends QueryStateCollector {
    @Input() datasetConfig: Dataset;
    scores = [];

    get imgPathPrefix() {
      return environment.imgPathPrefix;
    }

    addFilter() {
        this.store.dispatch({
          'type': MISSENSE_SCORE_ADD,
        });
    }

    removeFilter(index) {
        this.store.dispatch({
          'type': MISSENSE_SCORE_REMOVE,
          'payload': index
        });
    }

    private missenseScoresState: Observable<[MissenseScoresState, boolean,
                                             ValidationError[]]>;
    constructor(private store: Store<any>)  {
      super();
      this.missenseScoresState = toObservableWithValidation(
        MissenseScoresState, this.store.select('missenseScore')
      );
      this.missenseScoresState.subscribe(
        ([missenseScoresState, isValid, validationErrors]) => {
          this.scores = missenseScoresState.missenseScoresState;
        }
      );
    }

    ngOnInit() {
      this.store.dispatch({
        'type': MISSENSE_SCORES_INIT,
      });
    }
}
