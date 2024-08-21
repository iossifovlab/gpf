import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = [];

export const selectPersonIds = createFeatureSelector<object>('personIds');

export const setPersonIds = createAction(
  '[Genotype] Set person ids',
  props<{ personIds: string[] }>()
);

export const resetPersonIds = createAction(
  '[Genotype] Reset person ids'
);

export const personIdsReducer = createReducer(
  initialState,
  on(setPersonIds, (state, {personIds}) => personIds),
  on(resetPersonIds, state => []),
);
