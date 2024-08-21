import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetDatasetId {
  public static readonly type = '[Genotype] Set current dataset';
  public constructor(
    public selectedDatasetId: string
  ) {}
}

export interface DatasetModel {
    selectedDatasetId: string;
}

@State<DatasetModel>({
  name: 'datasetState',
  defaults: {
    selectedDatasetId: ''
  },
})
@Injectable()
export class DatasetState {
  @Action(SetDatasetId)
  public setDataset(
    ctx: StateContext<DatasetModel>,
    action: SetDatasetId
  ): void {
    ctx.patchState({
      selectedDatasetId: action.selectedDatasetId
    });
  }
}

import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
export const initialState = '';

export const selectDatasetId = createFeatureSelector<string>('datasetId');

export const setDatasetId = createAction(
  '[-] Set dataset id',
  props<{ datasetId: string }>()
);


export const datasetIdReducer = createReducer(
  initialState,
  on(setDatasetId, (state, {datasetId}) => datasetId),
);
