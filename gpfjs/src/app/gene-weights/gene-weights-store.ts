export const GENE_WEIGHTS_INIT = 'GENE_WEIGHTS_INIT';
export const GENE_WEIGHTS_RANGE_START_CHANGE = 'GENE_WEIGHTS_RANGE_START_CHANGE';
export const GENE_WEIGHTS_RANGE_END_CHANGE = 'GENE_WEIGHTS_RANGE_END_CHANGE';
export const GENE_WEIGHTS_CHANGE = 'GENE_WEIGHTS_CHANGE';

import { GeneWeights } from './gene-weights';
import { IsNotEmpty, IsNumber, Min, Max, ValidateIf } from "class-validator";
import { IsLessThanOrEqual } from "../utils/is-less-than-validator"
import { IsMoreThanOrEqual } from "../utils/is-more-than-validator"

export class GeneWeightsState {
  @IsNotEmpty()
  weight: GeneWeights;

  @ValidateIf(o => o.rangeStart !== null)
  @IsNumber()
  @IsLessThanOrEqual("rangeEnd")
  @IsMoreThanOrEqual("domainMin")
  @IsLessThanOrEqual("domainMax")
  rangeStart: number;

  @ValidateIf(o => o.rangeEnd !== null)
  @IsNumber()
  @IsMoreThanOrEqual("rangeStart")
  @IsMoreThanOrEqual("domainMin")
  @IsLessThanOrEqual("domainMax")
  rangeEnd: number;

  domainMin: number;
  domainMax: number;
};

const initialState: GeneWeightsState = {
  weight: null,
  rangeStart: 0,
  rangeEnd: 0,
  domainMin: 0,
  domainMax: 0
};

export function geneWeightsReducer(
  state: GeneWeightsState = null,
  action
): GeneWeightsState {

  switch (action.type) {
    case GENE_WEIGHTS_RANGE_START_CHANGE:
      return Object.assign({}, state,
        { rangeStart: action.payload });
    case GENE_WEIGHTS_RANGE_END_CHANGE:
      return Object.assign({}, state,
        { rangeEnd: action.payload });
    case GENE_WEIGHTS_CHANGE:
      return {
        weight: action.payload[0],
        rangeStart: null,
        rangeEnd: null,
        domainMin: action.payload[1],
        domainMax: action.payload[2]
      };
    case GENE_WEIGHTS_INIT:
      return initialState;
    default:
      return state;
  }
};
