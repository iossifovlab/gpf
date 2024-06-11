import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';
import { Dataset } from './datasets';

export class SetDataset {
  public static readonly type = '[Genotype] Set current dataset';
  public constructor(
    public selectedDataset: Dataset
  ) {}
}

export interface DatasetModel {
    selectedDataset: Dataset;
}

@State<DatasetModel>({
  name: 'datasetState',
  defaults: {
    selectedDataset: null
  },
})
@Injectable()
export class DatasetState {
  @Action(SetDataset)
  public setDataset(
    ctx: StateContext<DatasetModel>,
    action: SetDataset
  ): void {
    ctx.patchState({
      selectedDataset: action.selectedDataset
    });
  }
}
