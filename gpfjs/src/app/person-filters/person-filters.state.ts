import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { PersonFilterState } from './person-filters';
import { cloneDeep } from 'lodash';
import { reset } from 'app/users/state-actions';

export interface PersonAndFamilyFilters {
  familyFilters: PersonFilterState[];
  personFilters: PersonFilterState[];
}

export const initialState: PersonAndFamilyFilters = {
  familyFilters: null,
  personFilters: null,
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

export const updateFamilyFilter = createAction(
  '[Genotype] Update familyFilter value',
  props<{ familyFilter: PersonFilterState }>()
);

export const updatePersonFilter = createAction(
  '[Genotype] Update personFilter value',
  props<{ personFilter: PersonFilterState }>()
);

export const removeFamilyFilter = createAction(
  '[Genotype] Remove familyFilter value',
  props<{ familyFilter: PersonFilterState }>()
);

export const removePersonFilter = createAction(
  '[Genotype] Remove personFilter value',
  props<{ personFilter: PersonFilterState }>()
);

export const resetFamilyFilterStates = createAction(
  '[Genotype] Reset familyFilter states',
);

export const resetPersonFilterStates = createAction(
  '[Genotype] Reset personFilters states',
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
  on(updateFamilyFilter, (state, {familyFilter}) => {
    const stateClone = cloneDeep(state);
    if (!stateClone.familyFilters) {
      stateClone.familyFilters = [];
    }

    const newFamilyFilters = stateClone.familyFilters;
    const filterIndex = newFamilyFilters.findIndex(filter => filter.id === familyFilter.id);
    if (filterIndex !== -1) {
      newFamilyFilters[filterIndex] = familyFilter;
    } else {
      newFamilyFilters.push(familyFilter);
    }
    return {
      ...stateClone,
      familyFilters: newFamilyFilters,
    };
  }),
  on(updatePersonFilter, (state, {personFilter}) => {
    const stateClone = cloneDeep(state);
    if (!stateClone.personFilters) {
      stateClone.personFilters = [];
    }

    const newPersonFilters = stateClone.personFilters;
    const filterIndex = newPersonFilters.findIndex(filter => filter.id === personFilter.id);
    if (filterIndex !== -1) {
      newPersonFilters[filterIndex] = personFilter;
    } else {
      newPersonFilters.push(personFilter);
    }
    return {
      ...stateClone,
      personFilters: newPersonFilters,
    };
  }),
  on(removeFamilyFilter, (state, {familyFilter}) => {
    const stateClone = cloneDeep(state);
    const newFamilyFilters = stateClone.familyFilters;
    newFamilyFilters?.splice(newFamilyFilters.findIndex(filter => filter.id === familyFilter.id), 1);

    return {
      ...stateClone,
      familyFilters: newFamilyFilters,
    };
  }),
  on(removePersonFilter, (state, {personFilter}) => {
    const stateClone = cloneDeep(state);
    const newPersonFilters = stateClone.personFilters;
    newPersonFilters?.splice(newPersonFilters.findIndex(filter => filter.id === personFilter.id), 1);

    return {
      ...stateClone,
      personFilters: newPersonFilters,
    };
  }),
  on(resetFamilyFilterStates, (state) => ({...state, familyFilters: null})),
  on(resetPersonFilterStates, (state) => ({...state, personFilters: null})),
  on(reset, resetPersonFilters, (state) => initialState),
);

