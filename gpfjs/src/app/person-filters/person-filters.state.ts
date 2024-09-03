import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { PersonFilterState } from './person-filters';
import { cloneDeep } from 'lodash';
export const initialState: {
  familyFilters: PersonFilterState[];
  personFilters: PersonFilterState[];
} = {
  familyFilters: [],
  personFilters: [],
};

export const selectPersonFilters = createFeatureSelector<{
  familyFilters: PersonFilterState[];
  personFilters: PersonFilterState[];
}>('personFilters');

export const setFamilyFilters = createAction(
  '[Genotype] Set familyFilters values',
  props<{ familyFilters: PersonFilterState[] }>()
);

export const setPersonFilters = createAction(
  '[Genotype] Set personFilters values',
  props<{ personFilters: PersonFilterState[] }>()
);

export const resetPersonFilters = createAction(
  '[Genotype] Reset personFilters values',
);

export const personFiltersReducer = createReducer(
  initialState,
  on(setFamilyFilters, (state, {familyFilters}) => cloneDeep({
    ...state,
    familyFilters: familyFilters,
  })),
  on(setPersonFilters, (state, {personFilters}) => cloneDeep({
    ...state,
    personFilters: personFilters,
  })),
  on(resetPersonFilters, (state) => cloneDeep(initialState)),
);

