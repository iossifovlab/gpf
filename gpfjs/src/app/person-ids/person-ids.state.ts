import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPersonIds {
  public static readonly type = '[Genotype] Set person ids';
  public constructor(public personIds: string[]) {}
}

export interface PersonIdsModel {
  personIds: string[];
}

@State<PersonIdsModel>({
  name: 'personIdsState',
  defaults: {
    personIds: []
  },
})
@Injectable()
export class PersonIdsState {
  @Action(SetPersonIds)
  public changePersonIds(ctx: StateContext<PersonIdsModel>, action: SetPersonIds): void {
    ctx.patchState({
      personIds: action.personIds
    });
  }
}
