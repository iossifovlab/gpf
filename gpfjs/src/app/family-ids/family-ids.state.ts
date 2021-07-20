import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetFamilyIds {
  static readonly type = '[Genotype] Set family ids';
  constructor(public familyIds: string[]) {}
}

export interface FamilyIdsModel {
  familyIds: string[];
}

@State<FamilyIdsModel>({
  name: 'familyIdsState',
  defaults: {
    familyIds: []
  },
})
@Injectable()
export class FamilyIdsState {
  @Action(SetFamilyIds)
  changeFamilyIds(ctx: StateContext<FamilyIdsModel>, action: SetFamilyIds) {
    const state = ctx.getState();
    ctx.patchState({
      familyIds: action.familyIds
    });
  }
}
