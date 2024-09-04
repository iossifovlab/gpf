import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { PersonFilterState } from './person-filters';
import { cloneDeep } from 'lodash';
import { logout } from 'app/users/actions';

export interface PersonAndFamilyFilters {
  familyFilters: PersonFilterState[];
  personFilters: PersonFilterState[];
}

export const initialState: PersonAndFamilyFilters = {
  familyFilters: [],
  personFilters: [],
};

export const selectPersonFilters = createFeatureSelector<PersonAndFamilyFilters>('personFilters');

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
  on(logout, resetPersonFilters, (state) => cloneDeep(initialState)),
);

