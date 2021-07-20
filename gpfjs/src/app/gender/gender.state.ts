import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddGender {
  static readonly type = '[Genotype] Add Gender';
  constructor(public gender: string) {}
}

export class RemoveGender {
  static readonly type = '[Genotype] Remove Gender';
  constructor(public gender: string) {}
}

export class SetGender {
  static readonly type = '[Genotype] Set Gender';
  constructor(public gender: string[]) {}
}

export interface GenderModel {
  genders: string[];
}

@State<GenderModel>({
  name: 'genderState',
  defaults: {
    genders: ['male', 'female', 'unspecified']
  },
})
@Injectable()
export class GenderState {
  @Action(AddGender)
  addGender(ctx: StateContext<GenderModel>, action: AddGender) {
    const state = ctx.getState();
    ctx.patchState({
      genders: [...state.genders, action.gender]
    });
  }

  @Action(RemoveGender)
  removeGender(ctx: StateContext<GenderModel>, action: RemoveGender) {
    const state = ctx.getState();
    ctx.patchState({
      genders: state.genders.filter(gender => gender !== action.gender)
    });
  }

  @Action(SetGender)
  setEffectTypes(ctx: StateContext<GenderModel>, action: SetGender) {
    ctx.patchState({
      genders: Array.from(action.gender)
    });
  }
}
