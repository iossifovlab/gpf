import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';

export const zygosityFilterInitialState = '';

export const selectZygosityFilter = createFeatureSelector<string>('zygosityFilter');

export const setZygosityFilter = createAction(
  '[Genotype] Set zygosity filter',
  props<{ zygosityFilter: string }>()
);

export const resetZygosityFilter = createAction(
  '[Genotype] Reset zygosity filter'
);

export const zygosityFilterReducer = createReducer(
  zygosityFilterInitialState,
  on(setZygosityFilter, (state, { zygosityFilter }) => zygosityFilter),
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetZygosityFilter, state => zygosityFilterInitialState),
);
