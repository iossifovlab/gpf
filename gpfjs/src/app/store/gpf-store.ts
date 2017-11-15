import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';

export interface GpfState {
  geneWeights: GeneWeightsState;
  genomicScores: GenomicScoresState;
};

const reducers = {
  geneWeights: geneWeightsReducer,
};
