import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
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
  on(setErrors, (state, { errors }
  ) => {
    let updatedState: Errors[] = cloneDeep(state);
    const currentIndex = state.findIndex(e => e.componentId === errors.componentId);

    if (currentIndex === -1) {
      updatedState = [...state, cloneDeep(errors)];
      return updatedState;
    }
    updatedState[currentIndex] = {
      componentId: state[currentIndex].componentId,
      errors: [...state[currentIndex].errors, ...errors.errors]
    };
    return updatedState;
  }),
  on(resetErrors, (state, { componentId }) => state.filter(s => s.componentId !== componentId)),
  on(reset, resetAllErrors, (state) => cloneDeep(initialState)),
);
