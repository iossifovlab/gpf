// import { Injectable } from '@angular/core';
// import { State, Action, StateContext } from '@ngxs/store';

// export class SetRegionsFilter {
//   public static readonly type = '[Genotype] Set regions filter';
//   public constructor(public regionsFilters: string[]) {}
// }

// export interface RegionsFilterModel {
//   regionsFilters: string[];
// }

// @State<RegionsFilterModel>({
//   name: 'regionsFiltersState',
//   defaults: {
//     regionsFilters: []
//   },
// })
// @Injectable()
// export class RegionsFilterState {
//   @Action(SetRegionsFilter)
//   public addEffectType(ctx: StateContext<RegionsFilterModel>, action: SetRegionsFilter): void {
//     ctx.patchState({
//       regionsFilters: action.regionsFilters
//     });
//   }
// }


import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = [];

export const selectRegionsFilters = createFeatureSelector<object>('regionsFilter');

export const setRegionsFilters = createAction(
  '[Genotype] Set region filters',
  props<{ regionsFilter: string[] }>()
);

export const resetRegionsFilters = createAction(
  '[Genotype] Reset family ids'
);

export const regionsFiltersReducer = createReducer(
  initialState,
  on(setRegionsFilters, (state, {regionsFilter}) => regionsFilter),
  on(resetRegionsFilters, state => []),
);
