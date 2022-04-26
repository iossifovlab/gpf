import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPresentInChildValues {
  public static readonly type = '[Genotype] Set presentInChild values';
  public constructor(public presentInChild: Set<string>) {}
}

export interface PresentInChildModel {
  presentInChild: string[];
}

@State<PresentInChildModel>({
  name: 'presentInChildState',
  defaults: {
    presentInChild: ['proband only', 'proband and sibling']
  },
})
@Injectable()
export class PresentInChildState {
  @Action(SetPresentInChildValues)
  public setPresentInChildValue(ctx: StateContext<PresentInChildModel>, action: SetPresentInChildValues): void {
    ctx.patchState({
      presentInChild: [...action.presentInChild]
    });
  }
}
