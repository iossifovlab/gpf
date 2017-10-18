export const GENE_WEIGHTS_INIT = 'GENE_WEIGHTS_INIT';
export const GENE_WEIGHTS_RANGE_START_CHANGE = 'GENE_WEIGHTS_RANGE_START_CHANGE';
export const GENE_WEIGHTS_RANGE_END_CHANGE = 'GENE_WEIGHTS_RANGE_END_CHANGE';
export const GENE_WEIGHTS_CHANGE = 'GENE_WEIGHTS_CHANGE';

import { GeneWeights } from './gene-weights';
import { IsNotEmpty, IsNumber, Min, Max } from "class-validator";
import { IsLessThanOrEqual } from "../utils/is-less-than-validator"
import { IsMoreThanOrEqual } from "../utils/is-more-than-validator"

export class GeneWeightsState {
  @IsNotEmpty()
  weight: GeneWeights;

  @IsNumber()
  @Min(0)
  @IsLessThanOrEqual("rangeEnd")
  @IsMoreThanOrEqual("domainMin")
  rangeStart: number;

  @IsNumber()
  @Min(0)
  @IsMoreThanOrEqual("rangeStart")
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
        rangeStart: action.payload[1],
        rangeEnd: action.payload[2],
        domainMin: action.payload[1],
        domainMax: action.payload[2]
      };
    case GENE_WEIGHTS_INIT:
      return initialState;
    default:
      return state;
  }
};
