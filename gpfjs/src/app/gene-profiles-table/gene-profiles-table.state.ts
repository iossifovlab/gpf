// import { Injectable } from '@angular/core';
// import { State, Action, StateContext } from '@ngxs/store';

// export class SetGeneProfilesTabs {
//   public static readonly type = '[Genotype] Set gene profiles tabs';
//   public constructor(
//     public openedTabs: string[]
//   ) {}
// }
// export class SetGeneProfilesSearchValue {
//   public static readonly type = '[Genotype] Set gene profiles search value';
//   public constructor(
//     public searchValue: string
//   ) {}
// }
// export class SetGeneProfilesHighlightedRows {
//   public static readonly type = '[Genotype] Set gene profiles highlighted table rows';
//   public constructor(
//     public highlightedRows: string[]
//   ) {}
// }

// export class SetGeneProfilesSortBy {
//   public static readonly type = '[Genotype] Set gene profiles sorting element';
//   public constructor(
//     public sortBy: string
//   ) {}
// }

// export class SetGeneProfilesOrderBy {
//   public static readonly type = '[Genotype] Set gene profiles sort order';
//   public constructor(
//     public orderBy: string
//   ) {}
// }

// export class SetGeneProfilesHeader {
//   public static readonly type = '[Genotype] Set gene profiles config';
//   public constructor(
//     public headerLeaves: string[]
//   ) {}
// }

// export interface GeneProfilesModel {
//     openedTabs: string[];
//     searchValue: string;
//     highlightedRows: string[];
//     sortBy: string;
//     orderBy: string;
//     headerLeaves: string[];
// }

// @State<GeneProfilesModel>({
//   name: 'geneProfilesState',
//   defaults: {
//     openedTabs: [],
//     searchValue: '',
//     highlightedRows: [],
//     sortBy: '',
//     orderBy: 'desc',
//     headerLeaves: []
//   },
// })
// @Injectable()
// export class GeneProfilesState {
//   @Action(SetGeneProfilesTabs)
//   public setGeneProfilesTabs(
//     ctx: StateContext<GeneProfilesModel>,
//     action: SetGeneProfilesTabs
//   ): void {
//     ctx.patchState({
//       openedTabs: action.openedTabs
//     });
//   }

//   @Action(SetGeneProfilesSearchValue)
//   public setGeneProfilesSearchValue(
//     ctx: StateContext<GeneProfilesModel>,
//     action: SetGeneProfilesSearchValue
//   ): void {
//     ctx.patchState({
//       searchValue: action.searchValue
//     });
//   }

//   @Action(SetGeneProfilesHighlightedRows)
//   public setGeneProfilesHighlightedRows(
//     ctx: StateContext<GeneProfilesModel>,
//     action: SetGeneProfilesHighlightedRows
//   ): void {
//     ctx.patchState({
//       highlightedRows: action.highlightedRows
//     });
//   }

//   @Action(SetGeneProfilesSortBy)
//   public setGeneProfilesSortBy(
//     ctx: StateContext<GeneProfilesModel>,
//     action: SetGeneProfilesSortBy
//   ): void {
//     ctx.patchState({
//       sortBy: action.sortBy
//     });
//   }

//   @Action(SetGeneProfilesOrderBy)
//   public setGeneProfilesOrderBy(
//     ctx: StateContext<GeneProfilesModel>,
//     action: SetGeneProfilesOrderBy
//   ): void {
//     ctx.patchState({
//       orderBy: action.orderBy
//     });
//   }

//   @Action(SetGeneProfilesHeader)
//   public setGeneProfilesConfig(
//     ctx: StateContext<GeneProfilesModel>,
//     action: SetGeneProfilesHeader
//   ): void {
//     ctx.patchState({
//       headerLeaves: action.headerLeaves
//     });
//   }
// }

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
