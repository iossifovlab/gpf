import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
export const initialState = {};

export const selectErrors = createFeatureSelector<object>('errors');

export const setErrors = createAction(
  '[Errors] Set errors',
  props<{ componentId: string; errors: string[] }>()
);

export const resetErrors = createAction(
  '[Errors] Reset errors',
  props<{ componentId: string }>()
);

export const resetAllErrors = createAction(
  '[Errors] Reset all errors',
);

export const errorsReducer = createReducer(
  initialState,
  on(setErrors, (state, {componentId, errors}) => {
    const newState = {...state};
    newState[componentId] = errors;
    return newState;
  }),
  on(resetAllErrors, (state) => cloneDeep(initialState)),
);
