import { ActionReducer } from '@ngrx/store';
import { combineReducers } from '@ngrx/store';



import { DatasetsState, datasetsReducer } from '../dataset/dataset';
import { EffectTypesState, effectTypesReducer } from '../effecttypes/effecttypes';
import { GenderState, genderReducer } from '../gender/gender';
import { PedigreeSelectorState, pedigreeSelectorReducer } from '../pedigree-selector/pedigree-selector';
import { VariantTypesState, variantTypesReducer } from '../varianttypes/varianttypes';



export interface GpfState {
  datasets: DatasetsState;
  pedigreeSelector: PedigreeSelectorState;
  effectTypes: EffectTypesState;
  gender: GenderState;
  variantTypes: VariantTypesState;
};

const reducers = {
  datasets: datasetsReducer,
  pedigreeSelector: pedigreeSelectorReducer,
  effectTypes: effectTypesReducer,
  gender: genderReducer,
  variantTypes: variantTypesReducer,
};

const productionReducer: ActionReducer<GpfState> = combineReducers(reducers);

export function gpfReducer(state: any, action: any) {
  return productionReducer(state, action);
};
