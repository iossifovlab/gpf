import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPresentInChildValues {
  static readonly type = '[Genotype] Set presentInChild values';
  constructor(public presentInChild: Set<string>) {}
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
  setPresentInChildValue(ctx: StateContext<PresentInChildModel>, action: SetPresentInChildValues) {
    ctx.patchState({
      presentInChild: [...action.presentInChild]
    });
  }
}
