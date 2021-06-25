import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddPresentInChildValue {
  static readonly type = '[Genotype] Add presentInChild value';
  constructor(public presentInChild: string) {}
}

export class RemovePresentInChildValue {
  static readonly type = '[Genotype] Remove presentInChild value';
  constructor(public presentInChild: string) {}
}

export interface PresentInChildModel {
  presentInChild: string[];
}

@State<PresentInChildModel>({
  name: 'presentInChildState',
  defaults: {
    presentInChild: []
  },
})
@Injectable()
export class PresentInChildState {
  @Action(AddPresentInChildValue)
  addPresentInChildValue(ctx: StateContext<PresentInChildModel>, action: AddPresentInChildValue) {
    const state = ctx.getState();
    ctx.patchState({
      presentInChild: [...state.presentInChild, action.presentInChild]
    });
  }

  @Action(RemovePresentInChildValue)
  removePresentInChildValue(ctx: StateContext<PresentInChildModel>, action: RemovePresentInChildValue) {
    const state = ctx.getState();
    ctx.patchState({
      presentInChild: state.presentInChild.filter(inh => inh !== action.presentInChild)
    });
  }
}
