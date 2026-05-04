import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
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
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetFamilyIds, state => cloneDeep(initialState)),
);
