import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';

export interface GpfState {
  geneWeights: GeneWeightsState;
};

const reducers = {
  geneWeights: geneWeightsReducer,
};
