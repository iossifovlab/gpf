import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetRegionsFilter {
  public static readonly type = '[Genotype] Set regions filter';
  public constructor(public regionsFilters: string[]) {}
}

export interface RegionsFilterModel {
  regionsFilters: string[];
}

@State<RegionsFilterModel>({
  name: 'regionsFiltersState',
  defaults: {
    regionsFilters: []
  },
})
@Injectable()
export class RegionsFilterState {
  @Action(SetRegionsFilter)
  public addEffectType(ctx: StateContext<RegionsFilterModel>, action: SetRegionsFilter): void {
    ctx.patchState({
      regionsFilters: action.regionsFilters
    });
  }
}
