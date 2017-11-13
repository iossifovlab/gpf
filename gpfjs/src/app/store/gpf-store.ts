import { DatasetsState, datasetsReducer } from '../datasets/datasets';
import { PedigreeSelectorState, pedigreeSelectorReducer } from '../pedigree-selector/pedigree-selector';
import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';
import { GeneSetsState} from '../gene-sets/gene-sets-state';
import { PhenoFiltersState, phenoFiltersReducer } from '../pheno-filters/pheno-filters';

export interface GpfState {
  datasets: DatasetsState;
  pedigreeSelector: PedigreeSelectorState;
  geneWeights: GeneWeightsState;
  geneSets: GeneSetsState;
  phenoFilters: PhenoFiltersState;
};

const reducers = {
  datasets: datasetsReducer,
  pedigreeSelector: pedigreeSelectorReducer,
  geneWeights: geneWeightsReducer,
  phenoFilters: phenoFiltersReducer,
};
