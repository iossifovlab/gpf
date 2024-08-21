// import { Injectable } from '@angular/core';
// import { State, Action, StateContext } from '@ngxs/store';

// export class SetFamilyFilters {
//   public static readonly type = '[Genotype] Set familyFilters values';
//   public constructor(public filters: object[]) {}
// }

// export class SetPersonFilters {
//   public static readonly type = '[Genotype] Set personFilters values';
//   public constructor(public filters: object[]) {}
// }

// export interface PersonFiltersModel {
//   familyFilters: object[];
//   personFilters: object[];
// }

// @State<PersonFiltersModel>({
//   name: 'personFiltersState',
//   defaults: {
//     familyFilters: [],
//     personFilters: [],
//   },
// })
// @Injectable()
// export class PersonFiltersState {
//   @Action(SetFamilyFilters)
//   public setFamilyFilters(ctx: StateContext<PersonFiltersModel>, action: SetFamilyFilters): void {
//     ctx.patchState({
//       familyFilters: [...action.filters],
//       personFilters: ctx.getState().personFilters
//     });
//   }

//   @Action(SetPersonFilters)
//   public setPersonFilters(ctx: StateContext<PersonFiltersModel>, action: SetPersonFilters): void {
//     ctx.patchState({
//       familyFilters: ctx.getState().familyFilters,
//       personFilters: [...action.filters]
//     });
//   }
// }



import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { PersonFilter } from 'app/datasets/datasets';
import { PersonFilterState } from './person-filters';
export const initialState = [];

export const selectPersonFilters = createFeatureSelector<object>('personFilters');

export const setFamilyFilters = createAction(
  '[Genotype] Set familyFilters values',
  props<{ familyFilters: PersonFilterState[] }>()
);

export const setPersonFilters = createAction(
  '[Genotype] Set personFilters values',
  props<{ personFilters: PersonFilterState[] }>()
);

export const personFiltersReducer = createReducer(
  initialState,
  on(setFamilyFilters, (state, {familyFilters}) => familyFilters),
  on(setPersonFilters, (state, {personFilters}) => personFilters),
);

