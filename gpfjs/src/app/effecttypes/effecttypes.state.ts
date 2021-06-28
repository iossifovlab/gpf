import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddEffectType {
  static readonly type = '[Genotype] Add EffectType';
  constructor(public effectType: string) {}
}

export class RemoveEffectType {
  static readonly type = '[Genotype] Remove EffectType';
  constructor(public effectType: string) {}
}

export interface EffectTypeModel {
  effectTypes: string[];
}

@State<EffectTypeModel>({
  name: 'effecttypesState',
  defaults: {
    effectTypes: []
  },
})
@Injectable()
export class EffecttypesState {
  @Action(AddEffectType)
  addEffectType(ctx: StateContext<EffectTypeModel>, action: AddEffectType) {
    const state = ctx.getState();
    ctx.patchState({
      effectTypes: [...state.effectTypes, action.effectType]
    });
  }

  @Action(RemoveEffectType)
  removeEffectType(ctx: StateContext<EffectTypeModel>, action: RemoveEffectType) {
    const state = ctx.getState();
    ctx.patchState({
      effectTypes: state.effectTypes.filter(eff => eff !== action.effectType)
    });
  }
}
