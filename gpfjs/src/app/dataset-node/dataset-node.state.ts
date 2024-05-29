import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetExpandedDatasets {
  public static readonly type = '[Genotype] Set expanded datasets';
  public constructor(
    public expandedDatasets: Set<string>
  ) {}
}

export interface DatasetNodeModel {
    expandedDatasets: Set<string>;
}

@State<DatasetNodeModel>({
  name: 'datasetNodeState',
  defaults: {
    expandedDatasets: new Set<string>()
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
