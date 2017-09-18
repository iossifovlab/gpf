export const MISSENSE_SCORES_INIT = 'MISSENSE_SCORES_INIT';
export const MISSENSE_SCORES_RANGE_START_CHANGE = 'MISSENSE_SCORES_RANGE_START_CHANGE';
export const MISSENSE_SCORES_RANGE_END_CHANGE = 'MISSENSE_SCORES_RANGE_END_CHANGE';
export const MISSENSE_SCORES_CHANGE = 'MISSENSE_SCORES_CHANGE';
export const MISSENSE_SCORE_ADD = 'MISSENSE_SCORE_ADD';
export const MISSENSE_SCORE_REMOVE = 'MISSENSE_SCORE_REMOVE';

import { MissenseScoresHistogramData } from './missense-scores';
import { IsNotEmpty, IsNumber, Min, Max } from "class-validator";
import { IsLessThanOrEqual } from "../utils/is-less-than-validator"
import { IsMoreThanOrEqual } from "../utils/is-more-than-validator"

export class MissenseScoreState {
    @IsNotEmpty()
    histogramData: MissenseScoresHistogramData;

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

export class MissenseScoresState {
    missenseScoresState: MissenseScoreState[];
};

const initialState: MissenseScoresState = {
    missenseScoresState: []
};

export function missenseScoreReducer(
    state: MissenseScoresState = null,
    action
): MissenseScoresState {

    switch (action.type) {
    /*case MISSENSE_SCORES_RANGE_START_CHANGE:
      return Object.assign({}, state,
        { rangeStart: action.payload });
    case MISSENSE_SCORES_RANGE_END_CHANGE:
      return Object.assign({}, state,
        { rangeEnd: action.payload });*/
    case MISSENSE_SCORES_CHANGE:
        let newScore = {
            metric: action.payload[1],
            histogramData: action.payload[2],
            rangeStart: action.payload[3],
            rangeEnd: action.payload[4]
        };
        let newStateScore = state.missenseScoresState.map((item, index) => {
            if (index == action.payload[0]) {
                return newScore;
            }
            return item;
        });
        return Object.assign({}, state, { missenseScoresState: newStateScore });
    case MISSENSE_SCORE_ADD:
        let newStateAdd = [...state.missenseScoresState, new MissenseScoreState()];
        return Object.assign({}, state, { missenseScoresState: newStateAdd });
    case MISSENSE_SCORE_REMOVE:
        let newStateRemove = state.missenseScoresState.filter( (item, index) => index !== action.payload);
        return Object.assign({}, state, { missenseScoresState: newStateRemove });
    case MISSENSE_SCORES_INIT:
        return initialState;
    default:
        return state;
  }
};
