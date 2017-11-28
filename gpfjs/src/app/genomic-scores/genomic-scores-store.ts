import { GenomicScoresHistogramData } from './genomic-scores';
import { IsNotEmpty, IsNumber, Min, Max, ValidateIf, ValidateNested } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GenomicScoreState {
    histogramData: GenomicScoresHistogramData;

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

    metric: any;
    domainMin: any;
    domainMax: any;
    id: any;

    constructor() {
        this.histogramData = null;
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
