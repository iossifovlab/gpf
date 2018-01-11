import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { environment } from '../../environments/environment';

import { Observable } from 'rxjs/Observable';

import { GenomicScoreState, GenomicScoresState } from '../genomic-scores/genomic-scores-store';
import { StateRestoreService } from '../store/state-restore.service';


@Component({
    selector: 'gpf-genomic-scores-block',
    templateUrl: './genomic-scores-block.component.html',
    styleUrls: ['./genomic-scores-block.component.css'],
    providers: [{
        provide: QueryStateProvider,
        useExisting: forwardRef(() => GenomicScoresBlockComponent)
    }]
})
export class GenomicScoresBlockComponent extends QueryStateWithErrorsProvider implements OnInit {
    @Input() dataset: Dataset;
    genomicScoresState = new GenomicScoresState();
    scores = [];

    get imgPathPrefix() {
        return environment.imgPathPrefix;
    }

    trackById(index: number, data: any) {
        return data.id;
    }

    addFilter(genomicScoreState: GenomicScoreState = null) {
        if (!genomicScoreState) {
            genomicScoreState = new GenomicScoreState();
        }
        this.genomicScoresState.genomicScoresState.push(genomicScoreState);
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
            .take(1)
            .subscribe(state => {
                if (state['genomicScores'] && state['genomicScores'].length > 0) {
                    for (let score of state['genomicScores']) {
                        let genomicScore = new GenomicScoreState();
                        genomicScore.metric = score['metric'];
                        genomicScore.rangeStart = score['rangeStart'];
                        genomicScore.rangeEnd = score['rangeEnd'];
                        this.addFilter(genomicScore);
                    }
                }
            }
        );
    }

    getState() {
        return this.validateAndGetState(this.genomicScoresState)
            .map(genomicScoresState => {
                return {
                    genomicScores: genomicScoresState.genomicScoresState
                        .filter(el => el.histogramData)
                        .map(el => {
                            return {
                                metric: el.histogramData.metric,
                                rangeStart: el.rangeStart,
                                rangeEnd: el.rangeEnd
                            };
                        })
                };
            });
    }
}
