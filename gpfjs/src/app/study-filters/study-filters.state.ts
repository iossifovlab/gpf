import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
import { cloneDeep } from 'lodash';

export const initialState: string[] = [];

export const selectStudyFilters = createFeatureSelector<string[]>('studyFilters');

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
  on(reset, resetStudyFilters, state => cloneDeep(initialState)),
);
