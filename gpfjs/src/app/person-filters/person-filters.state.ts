import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { PersonFilterInterface } from './person-filters';
import { cloneDeep } from 'lodash';
export const initialState: {
  familyFilters: PersonFilterInterface[];
  personFilters: PersonFilterInterface[];
} = {
  familyFilters: [],
  personFilters: [],
};

export const selectPersonFilters = createFeatureSelector<{
  familyFilters: PersonFilterInterface[];
  personFilters: PersonFilterInterface[];
}>('personFilters');

export const setFamilyFilters = createAction(
  '[Genotype] Set familyFilters values',
  props<{ familyFilters: PersonFilterInterface[] }>()
);

export const setPersonFilters = createAction(
  '[Genotype] Set personFilters values',
  props<{ personFilters: PersonFilterInterface[] }>()
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
);

