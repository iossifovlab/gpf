import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';

export const initialState: string[] = ['trio', 'quad', 'multigenerational', 'simplex', 'multiplex', 'other'];

export const selectFamilyTypeFilter = createFeatureSelector<string[]>('familyTypeFilter');

export const setFamilyTypeFilter = createAction(
  '[Genotype] Set family type filter',
  props<{ familyTypeFilter: string[] }>()
);

export const resetFamilyTypeFilter = createAction(
  '[Genotype] Reset family type filter'
);

export const familyTypeFilterReducer = createReducer(
  initialState,
  on(setFamilyTypeFilter, (state: string[], {familyTypeFilter}) => cloneDeep(familyTypeFilter)),
  on(resetFamilyTypeFilter, state => cloneDeep(initialState)),
);
