import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { logout } from 'app/users/actions';
import { cloneDeep } from 'lodash';

export const initialState: string[] = [];

export const selectFamilyIds = createFeatureSelector<string[]>('familyIds');

export const setFamilyIds = createAction(
  '[Genotype] Set family ids',
  props<{ familyIds: string[] }>()
);

export const resetFamilyIds = createAction(
  '[Genotype] Reset family ids'
);

export const familyIdsReducer = createReducer(
  initialState,
  on(setFamilyIds, (state, {familyIds}) => cloneDeep(familyIds)),
  on(logout, resetFamilyIds, state => []),
);
