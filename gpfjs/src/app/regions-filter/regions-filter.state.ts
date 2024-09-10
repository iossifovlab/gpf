import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { logout } from 'app/users/actions';
import { cloneDeep } from 'lodash';

export const initialState: string[] = [];

export const selectRegionsFilters = createFeatureSelector<string[]>('regionsFilter');

export const setRegionsFilters = createAction(
  '[Genotype] Set region filters',
  props<{ regionsFilter: string[] }>()
);

export const resetRegionsFilters = createAction(
  '[Genotype] Reset region filters'
);

export const regionsFiltersReducer = createReducer(
  initialState,
  on(setRegionsFilters, (state, {regionsFilter}) => regionsFilter),
  on(logout, resetRegionsFilters, state => cloneDeep(initialState)),
);
