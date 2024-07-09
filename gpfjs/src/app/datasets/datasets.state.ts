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
