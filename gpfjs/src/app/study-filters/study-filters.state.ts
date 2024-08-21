import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = [];

export const selectStudyFilters = createFeatureSelector<object>('studyFilters');

export const setStudyFilters = createAction(
  '[Genotype] Set study filters',
  props<{ studyFilters: string[] }>()
);

export const resetStudyFilters = createAction(
  '[Genotype] Reset study filters'
);

export const studyFiltersReducer = createReducer(
  initialState,
  on(setStudyFilters, (state, {studyFilters}) => studyFilters),
  on(resetStudyFilters, state => []),
);
