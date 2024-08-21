import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
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


export const errorsReducer = createReducer(
  initialState,
  on(setErrors, (state, {componentId, errors}) => {
    const newState = {...state};
    newState[componentId] = errors;
    return newState;
  }),
  on(resetErrors, (state, {componentId}) => {
    const newState = {...state};
    delete newState[componentId];
    return newState;
  }),
);
