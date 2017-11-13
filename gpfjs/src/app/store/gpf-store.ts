import { DatasetsState, datasetsReducer } from '../datasets/datasets';
import { EffectTypesState, effectTypesReducer } from '../effecttypes/effecttypes';
import { GenderState, genderReducer } from '../gender/gender';
import { PedigreeSelectorState, pedigreeSelectorReducer } from '../pedigree-selector/pedigree-selector';
import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';
import { GeneSetsState} from '../gene-sets/gene-sets-state';
import { PhenoFiltersState, phenoFiltersReducer } from '../pheno-filters/pheno-filters';

export interface GpfState {
  datasets: DatasetsState;
  pedigreeSelector: PedigreeSelectorState;
  effectTypes: EffectTypesState;
  gender: GenderState;
  geneWeights: GeneWeightsState;
  geneSets: GeneSetsState;
  phenoFilters: PhenoFiltersState;
};

const reducers = {
  datasets: datasetsReducer,
  pedigreeSelector: pedigreeSelectorReducer,
  effectTypes: effectTypesReducer,
  gender: genderReducer,
  geneWeights: geneWeightsReducer,
  phenoFilters: phenoFiltersReducer,
};
