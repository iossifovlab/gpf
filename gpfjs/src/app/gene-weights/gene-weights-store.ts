import { GENES_BLOCK_TAB_DESELECT } from '../store/common';
export const RANGE_CHANGE = 'RANGE_CHANGE';

export interface GeneWeightsState {
  weight: string;
  rangeStart: number;
  rangeEnd: number;
};

const initialState: GeneWeightsState = {
  weight: null,
  rangeStart: 0,
  rangeEnd: 0
};

export function geneWeightsReducer(
  state: GeneWeightsState = initialState,
  action
): GeneWeightsState {

  switch (action.type) {
    case RANGE_CHANGE:
      return {
        weight: action.payload[0],
        rangeStart: action.payload[1],
        rangeEnd: action.payload[2]
      }
    case GENES_BLOCK_TAB_DESELECT:
      return initialState;
    default:
      return state;
  }
};
