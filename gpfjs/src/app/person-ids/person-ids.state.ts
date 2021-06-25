import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPersonIds {
  static readonly type = '[Genotype] Set person ids';
  constructor(public personIds: string) {}
}

export interface PersonIdsModel {
  personIds: string;
}

@State<PersonIdsModel>({
  name: 'personIdsState',
  defaults: {
    personIds: ''
  },
})
@Injectable()
export class PersonIdsState {
  @Action(SetPersonIds)
  changePersonIds(ctx: StateContext<PersonIdsModel>, action: SetPersonIds) {
    const state = ctx.getState();
    ctx.patchState({
      personIds: action.personIds
    });
  }
}
