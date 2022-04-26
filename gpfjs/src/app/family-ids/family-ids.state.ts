import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetFamilyIds {
  public static readonly type = '[Genotype] Set family ids';
  public constructor(public familyIds: string[]) {}
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
  public changeFamilyIds(ctx: StateContext<FamilyIdsModel>, action: SetFamilyIds): void {
    ctx.patchState({
      familyIds: action.familyIds
    });
  }
}
