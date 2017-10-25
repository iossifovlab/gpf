export const GENOMIC_SCORES_INIT = 'GENOMIC_SCORES_INIT';
export const GENOMIC_SCORES_RANGE_START_CHANGE = 'GENOMIC_SCORES_RANGE_START_CHANGE';
export const GENOMIC_SCORES_RANGE_END_CHANGE = 'GENOMIC_SCORES_RANGE_END_CHANGE';
export const GENOMIC_SCORES_CHANGE = 'GENOMIC_SCORES_CHANGE';
export const GENOMIC_SCORE_ADD = 'GENOMIC_SCORE_ADD';
export const GENOMIC_SCORE_REMOVE = 'GENOMIC_SCORE_REMOVE';

import { GenomicScoresHistogramData } from './genomic-scores';
import { IsNotEmpty, IsNumber, Min, Max } from "class-validator";
import { IsLessThanOrEqual } from "../utils/is-less-than-validator"
import { IsMoreThanOrEqual } from "../utils/is-more-than-validator"

export class GenomicScoreState {
    @IsNotEmpty()
    histogramData: GenomicScoresHistogramData;

    @IsNumber()
    @Min(0)
    @IsLessThanOrEqual("rangeEnd")
    @IsMoreThanOrEqual("histogramData.min")
    rangeStart: number;

    @IsNumber()
    @Min(0)
    @IsMoreThanOrEqual("rangeStart")
    @IsLessThanOrEqual("histogramData.max")
    rangeEnd: number;

    metric: any;

    constructor() {
        this.histogramData = null;
        this.rangeStart = null;
        this.rangeEnd = null;
    }
};

export class GenomicScoresState {
    genomicScoresState: GenomicScoreState[];
};

const initialState: GenomicScoresState = {
    genomicScoresState: []
};

export function genomicScoresReducer(
    state: GenomicScoresState = null,
    action
): GenomicScoresState {

    switch (action.type) {
    case GENOMIC_SCORES_RANGE_START_CHANGE: {
        let index = action.payload[0]
        let newScore = Object.assign({}, state.genomicScoresState[index],
            { rangeStart: action.payload[1] })
        let newStateScore = state.genomicScoresState.map((item, index) => {
            if (index == action.payload[0]) {
                return newScore;
            }
            return item;
        });
        return Object.assign({}, state, { genomicScoresState: newStateScore });
    }
    case GENOMIC_SCORES_RANGE_END_CHANGE: {
        let index = action.payload[0]
        let newScore = Object.assign({}, state.genomicScoresState[index],
            { rangeEnd: action.payload[1] })
        let newStateScore = state.genomicScoresState.map((item, index) => {
            if (index == action.payload[0]) {
                return newScore;
            }
            return item;
        });
        return Object.assign({}, state, { genomicScoresState: newStateScore });
    }
    case GENOMIC_SCORES_CHANGE: {
        let newScore = {
            metric: action.payload[1],
            histogramData: action.payload[2],
            rangeStart: null,
            rangeEnd: null
        };
        let newStateScore = state.genomicScoresState.map((item, index) => {
            if (index == action.payload[0]) {
                return newScore;
            }
            return item;
        });
        return Object.assign({}, state, { genomicScoresState: newStateScore });
    }
    case GENOMIC_SCORE_ADD: {
        let newStateAdd = [...state.genomicScoresState, new GenomicScoreState()];
        return Object.assign({}, state, { genomicScoresState: newStateAdd });
    }
    case GENOMIC_SCORE_REMOVE: {
        let newStateRemove = state.genomicScoresState.filter( (item, index) => index !== action.payload);
        return Object.assign({}, state, { genomicScoresState: newStateRemove });
    }
    case GENOMIC_SCORES_INIT:
        return initialState;
    default:
        return state;
  }
};
