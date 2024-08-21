// import { Injectable } from '@angular/core';
// import { State, Action, StateContext } from '@ngxs/store';

// export class SetExpandedDatasets {
//   public static readonly type = '[Genotype] Set expanded datasets';
//   public constructor(
//     public expandedDatasets: string[]
//   ) {}
// }

// export interface DatasetNodeModel {
//     expandedDatasets: string[];
// }

// @State<DatasetNodeModel>({
//   name: 'datasetNodeState',
//   defaults: {
//     expandedDatasets: []
//   },
// })
// @Injectable()
// export class DatasetNodeState {
//   @Action(SetExpandedDatasets)
//   public setExpandedDatasets(
//     ctx: StateContext<DatasetNodeModel>,
//     action: SetExpandedDatasets
//   ): void {
//     ctx.patchState({
//       expandedDatasets: action.expandedDatasets
//     });
//   }
// }

import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = [];

export const selectExpandedDatasets = createFeatureSelector<object>('expandedDatasets');

export const setExpandedDatasets = createAction(
  '[Genotype] Set expanded datasets',
  props<{ expandedDatasets: string[] }>()
);

export const expandedDatasetsReducer = createReducer(
  initialState,
  on(setExpandedDatasets, (state, {expandedDatasets}) => expandedDatasets),
);
