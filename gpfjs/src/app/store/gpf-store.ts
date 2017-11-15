import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';
import { PhenoFiltersState } from '../pheno-filters/pheno-filters';

export interface GpfState {
  geneWeights: GeneWeightsState;
  phenoFilters: PhenoFiltersState;
};

const reducers = {
  geneWeights: geneWeightsReducer,
};
