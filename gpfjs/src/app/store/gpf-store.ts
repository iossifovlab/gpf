import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';
import { GeneSetsState} from '../gene-sets/gene-sets-state';
import { PhenoFiltersState, phenoFiltersReducer } from '../pheno-filters/pheno-filters';

export interface GpfState {
  geneWeights: GeneWeightsState;
  geneSets: GeneSetsState;
  phenoFilters: PhenoFiltersState;
};

const reducers = {
  geneWeights: geneWeightsReducer,
  phenoFilters: phenoFiltersReducer,
};
