import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddEffectType {
  public static readonly type = '[Genotype] Add EffectType';
  public constructor(public effectType: string) {}
}

export class RemoveEffectType {
  public static readonly type = '[Genotype] Remove EffectType';
  public constructor(public effectType: string) {}
}

export class SetEffectTypes {
  public static readonly type = '[Genotype] Set effect types';
  public constructor(public effectTypes: Set<string>) {}
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
  public addEffectType(ctx: StateContext<EffectTypeModel>, action: AddEffectType): void {
    const state = ctx.getState();
    ctx.patchState({
      effectTypes: [...state.effectTypes, action.effectType]
    });
  }

  @Action(RemoveEffectType)
  public removeEffectType(ctx: StateContext<EffectTypeModel>, action: RemoveEffectType): void {
    const state = ctx.getState();
    ctx.patchState({
      effectTypes: state.effectTypes.filter(eff => eff !== action.effectType)
    });
  }

  @Action(SetEffectTypes)
  public setEffectTypes(ctx: StateContext<EffectTypeModel>, action: SetEffectTypes): void {
    ctx.patchState({
      effectTypes: Array.from(action.effectTypes)
    });
  }
}
