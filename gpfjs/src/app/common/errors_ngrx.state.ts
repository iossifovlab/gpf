import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
export const initialState: Errors[] = [];
export interface Errors {
  componentId: string;
  errors: string[];
}

export const selectErrors = createFeatureSelector<Errors[]>('errors');

export const setErrors = createAction(
  '[Errors] Set errors',
  props<{ errors: Errors }>()
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
  on(setErrors, (state, { errors }) => {
    if (!state.length) {
      state = [errors];
      return state;
    }
    state.forEach(s => {
      if (s.componentId === errors.componentId) {
        s = {componentId: s.componentId, errors: [...s.errors, ...errors.errors]};
      } else {
        state = [...state, errors];
      }
    });
    return state;
  }),
  on(resetErrors, (state, { componentId }) => state.filter(s => s.componentId !== componentId)
  ),
  on(resetAllErrors, (state) => cloneDeep(initialState)),
);
