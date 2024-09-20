import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = '';

export const selectDatasetId = createFeatureSelector<string>('datasetId');

export const setDatasetId = createAction(
  '[-] Set dataset id',
  props<{ datasetId: string }>()
);

export const resetDatasetId = createAction(
  '[Errors] Reset dataset id',
);

export const datasetIdReducer = createReducer(
  initialState,
  on(setDatasetId, (state, {datasetId}) => datasetId),
  on(resetDatasetId, (state,) => initialState),
);
