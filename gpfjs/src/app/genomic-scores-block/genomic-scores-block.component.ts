import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateProvider } from '../query/query-state-provider';
import { environment } from '../../environments/environment';

import { Observable } from 'rxjs/Observable';

import { GenomicScoreState, GenomicScoresState } from '../genomic-scores/genomic-scores-store';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { StateRestoreService } from '../store/state-restore.service';
import { transformAndValidate } from 'class-transformer-validator';


@Component({
    selector: 'gpf-genomic-scores-block',
    templateUrl: './genomic-scores-block.component.html',
    styleUrls: ['./genomic-scores-block.component.css'],
    providers: [{
        provide: QueryStateProvider,
        useExisting: forwardRef(() => GenomicScoresBlockComponent)
    }]
})
export class GenomicScoresBlockComponent extends QueryStateProvider implements OnInit {
    @Input() dataset: Dataset;
    genomicScoresState = new GenomicScoresState();
    scores = [];

    get imgPathPrefix() {
        return environment.imgPathPrefix;
    }

    trackById(index: number, data: any) {
        return data.id;
    }

    addFilter() {
        this.genomicScoresState.genomicScoresState.push(new GenomicScoreState());
    }

    removeFilter(genomicScore: GenomicScoreState) {
        this.genomicScoresState.genomicScoresState = this.genomicScoresState
            .genomicScoresState.filter(gs => gs !== genomicScore);
    }

    constructor(
        private stateRestoreService: StateRestoreService
    ) {
        super();
    }

    ngOnInit() {
        this.stateRestoreService.getState(this.constructor.name)
            .subscribe(state => {
                if (state['genomicScores']) {
                    for (let score of state['genomicScores']) {
                        if (score['metric']) {
                            this.addFilter();
                        }
                    }
                }
            }
        );
    }

    getState() {
        return toValidationObservable(this.genomicScoresState)
            .map(genomicScoresState => {
                return {
                    genomicScores: genomicScoresState.genomicScoresState
                        .map(el => {
                            transformAndValidate(GenomicScoreState, el);

                            if (el.histogramData === null) {
                                return {};
                            }
                            return {
                                metric: el.histogramData.metric,
                                rangeStart: el.rangeStart,
                                rangeEnd: el.rangeEnd
                            };
                        })
                };
            })
            .catch(errors => {
                return Observable.throw(
                    `${this.constructor.name}: invalid state`
                );
            });
    }
}
