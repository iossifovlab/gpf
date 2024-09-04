import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { logout } from 'app/users/actions';
import { cloneDeep } from 'lodash';
export const initialState: string[] = [];

export const selectGeneSymbols = createFeatureSelector<string[]>('geneSymbols');

export const setGeneSymbols = createAction(
  '[Genotype] Set gene symbols',
  props<{ geneSymbols: string[] }>()
);

export const resetGeneSymbols = createAction(
  '[Genotype] Reset gene symbols'
);

export const geneSymbolsReducer = createReducer(
  initialState,
  on(setGeneSymbols, (state: string[], { geneSymbols }) => [...geneSymbols]),
  on(logout, resetGeneSymbols, state => cloneDeep(initialState)),
);
