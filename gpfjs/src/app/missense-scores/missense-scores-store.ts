export const MISSENSE_SCORES_INIT = 'MISSENSE_SCORES_INIT';
export const MISSENSE_SCORES_RANGE_START_CHANGE = 'MISSENSE_SCORES_RANGE_START_CHANGE';
export const MISSENSE_SCORES_RANGE_END_CHANGE = 'MISSENSE_SCORES_RANGE_END_CHANGE';
export const MISSENSE_SCORES_CHANGE = 'MISSENSE_SCORES_CHANGE';

import { MissenseScoresHistogramData } from './missense-scores';
import { IsNotEmpty, IsNumber, Min, Max } from "class-validator";
import { IsLessThanOrEqual } from "../utils/is-less-than-validator"
import { IsMoreThanOrEqual } from "../utils/is-more-than-validator"

export class MissenseScoresState {
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
};

const initialState: MissenseScoresState = {
  histogramData: null,
  rangeStart: 0,
  rangeEnd: 0
};

export function missenseScoreReducer(
  state: MissenseScoresState = null,
  action
): MissenseScoresState {

  switch (action.type) {
    case MISSENSE_SCORES_RANGE_START_CHANGE:
      return Object.assign({}, state,
        { rangeStart: action.payload });
    case MISSENSE_SCORES_RANGE_END_CHANGE:
      return Object.assign({}, state,
        { rangeEnd: action.payload });
    case MISSENSE_SCORES_CHANGE:
      return {
        histogramData: action.payload[0],
        rangeStart: action.payload[1],
        rangeEnd: action.payload[2]
      };
    case MISSENSE_SCORES_INIT:
      return initialState;
    default:
      return state;
  }
};
