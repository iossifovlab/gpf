import { IsNotEmpty, IsNumber, Min, Max, ValidateIf, ValidateNested } from 'class-validator';
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

    constructor() {
        this.score = null;
        this.rangeStart = null;
        this.rangeEnd = null;
    }
};

export class GenomicScoresState {
    @ValidateNested({
        each: true
    })
    genomicScoresState: GenomicScoreState[] = [];
};
