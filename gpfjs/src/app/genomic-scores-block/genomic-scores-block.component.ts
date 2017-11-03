import { Component, Input, forwardRef } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateProvider } from '../query/query-state-provider';
import { environment } from '../../environments/environment';

import { Observable }        from 'rxjs/Observable';
import { ValidationError } from "class-validator";
import { GenomicScoresState, GENOMIC_SCORES_INIT, GENOMIC_SCORES_CHANGE,
         GENOMIC_SCORES_RANGE_START_CHANGE, GENOMIC_SCORES_RANGE_END_CHANGE,
         GENOMIC_SCORE_ADD, GENOMIC_SCORE_REMOVE
 } from '../genomic-scores/genomic-scores-store';
 import { Store } from '@ngrx/store';
 import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
 import { StateRestoreService } from '../store/state-restore.service';


@Component({
  selector: 'gpf-genomic-scores-block',
  templateUrl: './genomic-scores-block.component.html',
  styleUrls: ['./genomic-scores-block.component.css'],
  providers: [{provide: QueryStateProvider,
               useExisting: forwardRef(() => GenomicScoresBlockComponent) }]
})
export class GenomicScoresBlockComponent extends QueryStateProvider {
    @Input() datasetConfig: Dataset;
    private filterId = 0;
    scores = [];

    get imgPathPrefix() {
      return environment.imgPathPrefix;
    }

    trackById(index: number, data: any) {
        return data.id;
    }

    addFilter() {
        this.store.dispatch({
          'type': GENOMIC_SCORE_ADD,
          'payload': this.filterId
        });
        this.filterId++;
    }

    removeFilter(index) {
        this.store.dispatch({
          'type': GENOMIC_SCORE_REMOVE,
          'payload': index
        });
    }

    private genomicScoresState: Observable<[GenomicScoresState, boolean,
                                             ValidationError[]]>;
    constructor(
        private store: Store<any>,
        private stateRestoreService: StateRestoreService
    )  {
      super();
      this.genomicScoresState = toObservableWithValidation(
        GenomicScoresState, this.store.select('genomicScores')
      );
      this.genomicScoresState.subscribe(
        ([genomicScoresState, isValid, validationErrors]) => {
          this.scores = genomicScoresState.genomicScoresState;
        }
      );
    }

    ngOnInit() {
        this.store.dispatch({
            'type': GENOMIC_SCORES_INIT,
        });

        this.stateRestoreService.getState(this.constructor.name).subscribe(
            (state) => {
                console.log(state['genomicScores'])
                if (state['genomicScores']) {
                    for (let score of state['genomicScores']) {
                        if (score['metric']) {
                            this.store.dispatch({
                                'type': GENOMIC_SCORE_ADD,
                            });
                        }
                    }
                }
            }
        );
    }

    getState() {
        return this.genomicScoresState.take(1).map(
            ([genomicScoresState, isValid, validationErrors]) => {
                if (!isValid) {
                    //  this.flashingAlert = true;
                    //  setTimeout(()=>{ this.flashingAlert = false }, 1000)
                    throw "invalid geneWeights state"
                }

                return {
                    genomicScores: genomicScoresState.genomicScoresState.map(el => {
                        if (el.histogramData === null) {
                            return {}
                        }
                        return {
                            metric: el.histogramData.metric,
                            rangeStart: el.rangeStart,
                            rangeEnd: el.rangeEnd
                        }
                    })
                }
            }
        )
    }
}
