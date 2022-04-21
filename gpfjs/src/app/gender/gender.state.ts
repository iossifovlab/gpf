import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddGender {
  public static readonly type = '[Genotype] Add Gender';
  public constructor(public gender: string) {}
}

export class RemoveGender {
  public static readonly type = '[Genotype] Remove Gender';
  public constructor(public gender: string) {}
}

export class SetGender {
  public static readonly type = '[Genotype] Set Gender';
  public constructor(public gender: string[]) {}
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
  public addGender(ctx: StateContext<GenderModel>, action: AddGender): void {
    const state = ctx.getState();
    ctx.patchState({
      genders: [...state.genders, action.gender]
    });
  }

  @Action(RemoveGender)
  public removeGender(ctx: StateContext<GenderModel>, action: RemoveGender): void {
    const state = ctx.getState();
    ctx.patchState({
      genders: state.genders.filter(gender => gender !== action.gender)
    });
  }

  @Action(SetGender)
  public setGender(ctx: StateContext<GenderModel>, action: SetGender): void {
    ctx.patchState({
      genders: Array.from(action.gender)
    });
  }
}
