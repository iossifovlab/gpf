import { IsNotEmpty, IsNumber, ValidateIf, ValidateNested } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

import { GenomicScores } from '../genomic-scores-block/genomic-scores-block';

export class GenomicScoreState {
    @IsNotEmpty()
    score: GenomicScores;

    @ValidateIf(o => o.rangeStart !== null)
    @IsNumber()
    @IsLessThanOrEqual('rangeEnd')
    @IsMoreThanOrEqual('domainMin')
    @IsLessThanOrEqual('domainMax')
    rangeStart: number;


    @ValidateIf(o => o.rangeEnd !== null)
    @IsNumber()
    @IsMoreThanOrEqual('rangeStart')
    @IsMoreThanOrEqual('domainMin')
    @IsLessThanOrEqual('domainMax')
    rangeEnd: number;

    domainMin: any;
    domainMax: any;

    changeDomain(score: GenomicScores) {
        if (this.score.domain != null) {
            this.domainMin = score.domain[0];
            this.domainMax = score.domain[1];
        } else {
            this.domainMin = score.bins[0];
            this.domainMax = score.bins[score.bins.length - 1];
        }
    }

    constructor(score?: GenomicScores) {
        if (score) {
            this.score = score;
            this.changeDomain(score);
        } else { 
            this.score = null;
        }
        this.rangeStart = null;
        this.rangeEnd = null;
    }
}

export class GenomicScoresState {
    @ValidateNested({
        each: true
    })
    genomicScoresState: GenomicScoreState[] = [];
}
