import { ActionReducer } from '@ngrx/store';
import { combineReducers } from '@ngrx/store';



import { DatasetsState, datasetsReducer } from '../datasets/datasets';
import { EffectTypesState, effectTypesReducer } from '../effecttypes/effecttypes';
import { GenderState, genderReducer } from '../gender/gender';
import { PedigreeSelectorState, pedigreeSelectorReducer } from '../pedigree-selector/pedigree-selector';
import { VariantTypesState, variantTypesReducer } from '../varianttypes/varianttypes';
import { GeneWeightsState, geneWeightsReducer } from '../gene-weights/gene-weights-store';
import { PresentInChildState, presentInChildReducer } from '../present-in-child/present-in-child';
import { PresentInParentState, presentInParentReducer } from '../present-in-parent/present-in-parent';
import { GeneSymbolsState, geneSymbolsReducer } from '../gene-symbols/gene-symbols';
import { RegionsFilterState, regionsFilterReducer } from '../regions-filter/regions-filter';
import { GeneSetsState, geneSetsReducer } from '../gene-sets/gene-sets-state';
import { UsersState, usersReducer } from '../users/users-store';
import { StudyTypesState, studyTypesReducer } from '../study-types/study-types';

export interface GpfState {
  datasets: DatasetsState;
  pedigreeSelector: PedigreeSelectorState;
  effectTypes: EffectTypesState;
  gender: GenderState;
  variantTypes: VariantTypesState;
  geneWeights: GeneWeightsState;
  presentInChild: PresentInChildState;
  presentInParent: PresentInParentState;
  geneSymbols: GeneSymbolsState;
  regionsFilter: RegionsFilterState;
  geneSets: GeneSetsState;
  users: UsersState;
};

const reducers = {
  datasets: datasetsReducer,
  pedigreeSelector: pedigreeSelectorReducer,
  effectTypes: effectTypesReducer,
  gender: genderReducer,
  variantTypes: variantTypesReducer,
  geneWeights: geneWeightsReducer,
  presentInChild: presentInChildReducer,
  presentInParent: presentInParentReducer,
  geneSymbols: geneSymbolsReducer,
  regionsFilter: regionsFilterReducer,
  geneSets: geneSetsReducer,
  users: usersReducer,
  studyTypes: studyTypesReducer,
};

const productionReducer: ActionReducer<GpfState> = combineReducers(reducers);

export function gpfReducer(state: any, action: any) {
  return productionReducer(state, action);
};
