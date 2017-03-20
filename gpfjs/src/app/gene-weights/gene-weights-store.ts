export const GENE_WEIGHTS_RANGE_CHANGE = 'GENE_WEIGHTS_RANGE_CHANGE';
export const GENE_WEIGHTS_INIT = 'GENE_WEIGHTS_INIT';

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
  state: GeneWeightsState = null,
  action
): GeneWeightsState {

  switch (action.type) {
    case GENE_WEIGHTS_RANGE_CHANGE:
      return {
        weight: action.payload[0],
        rangeStart: action.payload[1],
        rangeEnd: action.payload[2]
      };
    case GENE_WEIGHTS_INIT:
      return initialState;
    default:
      return state;
  }
};
