import { DatasetsState, datasetsReducer } from '../datasets/datasets';
import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';
import { GeneSetsState} from '../gene-sets/gene-sets-state';
import { PhenoFiltersState, phenoFiltersReducer } from '../pheno-filters/pheno-filters';

export interface GpfState {
  datasets: DatasetsState;
  geneWeights: GeneWeightsState;
  geneSets: GeneSetsState;
  phenoFilters: PhenoFiltersState;
};

const reducers = {
  datasets: datasetsReducer,
  geneWeights: geneWeightsReducer,
  phenoFilters: phenoFiltersReducer,
};
