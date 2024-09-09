import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { logout } from 'app/users/actions';
import { cloneDeep } from 'lodash';

export interface PedigreeSelector {
  id: string;
  checkedValues: string[];
}

export const initialState: PedigreeSelector = null;

export const selectPedigreeSelector =
  createFeatureSelector<PedigreeSelector>('pedigreeSelector');

export const setPedigreeSelector = createAction(
  '[Genotype] Set pedigreeSelector',
  props<{ pedigreeSelector: PedigreeSelector}>()
);

export const resetPedigreeSelector = createAction(
  '[Genotype] Reset pedigreeSelector'
);

export const pedigreeSelectorReducer = createReducer(
  initialState,
  on(setPedigreeSelector, (state: PedigreeSelector, { pedigreeSelector }) => cloneDeep(pedigreeSelector)),
  on(logout, resetPedigreeSelector, state => cloneDeep(initialState))
);
