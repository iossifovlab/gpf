import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';

export interface GeneProfiles {
  openedTabs: string[];
  searchValue: string;
  highlightedRows: string[];
  sortBy: string;
  orderBy: string;
  headerLeaves: string[];
}

export const initialState: GeneProfiles = {
  openedTabs: [],
  searchValue: '',
  highlightedRows: [],
  sortBy: '',
  orderBy: 'desc',
  headerLeaves: []
};

export const selectGeneProfiles =
  createFeatureSelector<GeneProfiles>('geneProfiles');

export const setGeneProfilesOpenedTabs = createAction(
  '[Genotype] Set gene profiles tabs',
  props<{ openedTabs: string[] }>()
);

export const setGeneProfilesSearchValue = createAction(
  '[Genotype] Set gene profiles search value',
  props<{ searchValue: string }>()
);

export const setGeneProfilesHighlightedRows = createAction(
  '[Genotype] Set gene profiles highlighted rows',
  props<{ highlightedRows: string[]}>()
);

export const setGeneProfilesSortBy = createAction(
  '[Genotype] Set gene profiles sort by',
  props<{ sortBy: string }>()
);

export const setGeneProfilesOrderBy = createAction(
  '[Genotype] Set gene profiles order by',
  props<{ orderBy: string }>()
);

export const setGeneProfilesHeaderLeaves = createAction(
  '[Genotype] Set gene profiles header leaves',
  props<{ headerLeaves: string[]}>()
);

export const setGeneProfilesValues = createAction(
  '[Genotype] Set gene profiles values',
  props<{ geneProfiles: GeneProfiles}>()
);

export const resetGeneProfilesValues = createAction(
  '[Genotype] Reset gene profiels values'
);

export const geneProfilesReducer = createReducer(
  initialState,
  on(setGeneProfilesOpenedTabs, (state, { openedTabs }) => ({
    ...state,
    openedTabs: cloneDeep(openedTabs)
  })),
  on(setGeneProfilesSearchValue, (state, { searchValue }) => ({
    ...state,
    searchValue: searchValue
  })),
  on(setGeneProfilesHighlightedRows, (state, { highlightedRows }) => ({
    ...state,
    highlightedRows: cloneDeep(highlightedRows)
  })),
  on(setGeneProfilesSortBy, (state, { sortBy }) => ({
    ...state,
    sortBy: sortBy
  })),
  on(setGeneProfilesOrderBy, (state, { orderBy }) => ({
    ...state,
    orderBy: orderBy
  })),
  on(setGeneProfilesHeaderLeaves, (state, { headerLeaves }) => ({
    ...state,
    headerLeaves: cloneDeep(headerLeaves)
  })),
  on(setGeneProfilesValues, (state: GeneProfiles, { geneProfiles }) => cloneDeep(geneProfiles)),
  on(resetGeneProfilesValues, state => cloneDeep(initialState))
);
