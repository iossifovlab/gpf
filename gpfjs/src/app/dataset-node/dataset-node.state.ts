import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetExpandedDatasets {
  public static readonly type = '[Genotype] Set expanded datasets';
  public constructor(
    public expandedDatasets: string[]
  ) {}
}

export interface DatasetNodeModel {
    expandedDatasets: string[];
}

@State<DatasetNodeModel>({
  name: 'datasetNodeState',
  defaults: {
    expandedDatasets: []
  },
})
@Injectable()
export class DatasetNodeState {
  @Action(SetExpandedDatasets)
  public setExpandedDatasets(
    ctx: StateContext<DatasetNodeModel>,
    action: SetExpandedDatasets
  ): void {
    ctx.patchState({
      expandedDatasets: action.expandedDatasets
    });
  }
}
