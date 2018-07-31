import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { environment } from '../../environments/environment';

import { GenomicScoreState, GenomicScoresState } from '../genomic-scores/genomic-scores-store';
import { GenomicScoresBlockService } from './genomic-scores-block.service';
import { StateRestoreService } from '../store/state-restore.service';
import { GenomicScores } from './genomic-scores-block';


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
    genomicScoresState = new GenomicScoresState();
    scores = [];
    genomicScoresArray: GenomicScores[];

    get imgPathPrefix() {
        return environment.imgPathPrefix;
    }

    trackById(index: number, data: any) {
        return data.id;
    }

    addFilter(genomicScoreState: GenomicScoreState = null) {
        if (!genomicScoreState) {
            genomicScoreState = new GenomicScoreState();
            genomicScoreState.score = this.genomicScoresArray[0];
            genomicScoreState.domainMin = genomicScoreState.score.bins[0];
            genomicScoreState.domainMax =
              genomicScoreState.score.bins[genomicScoreState.score.bins.length - 1];
        }
        this.genomicScoresState.genomicScoresState.push(genomicScoreState);
    }

    removeFilter(genomicScore: GenomicScoreState) {
        this.genomicScoresState.genomicScoresState = this.genomicScoresState
            .genomicScoresState.filter(gs => gs !== genomicScore);
    }

    constructor(
        private genomicScoresBlockService: GenomicScoresBlockService,
        private stateRestoreService: StateRestoreService
    ) {
        super();
    }

    restoreStateSubscribe() {
        this.stateRestoreService.getState(this.constructor.name)
            .take(1)
            .subscribe(state => {
                if (state['genomicScores'] && state['genomicScores'].length > 0) {
                    for (let score of state['genomicScores']) {
                        let genomicScore = new GenomicScoreState();
                        genomicScore.score = this.genomicScoresArray
                                                 .find(el => el['score'] === score['metric']);
                        genomicScore.rangeStart = score['rangeStart'];
                        genomicScore.rangeEnd = score['rangeEnd'];
                        genomicScore.domainMin = genomicScore.score.bins[0];
                        genomicScore.domainMax =
                          genomicScore.score.bins[genomicScore.score.bins.length - 1];
                        this.addFilter(genomicScore);
                    }
                }
            });
    }

    ngOnInit() {
        this.genomicScoresBlockService.getGenomicScores()
        .take(1)
        .subscribe(genomicScores => {
            this.genomicScoresArray = genomicScores

            this.restoreStateSubscribe();
        });
    }

    getState() {
        return this.validateAndGetState(this.genomicScoresState)
            .map(genomicScoresState => {
                return {
                    genomicScores: genomicScoresState.genomicScoresState
                        .filter(el => el.score)
                        .map(el => {
                            return {
                                metric: el.score.score,
                                rangeStart: el.rangeStart,
                                rangeEnd: el.rangeEnd
                            };
                        })
                };
            });
    }
}
