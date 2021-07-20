import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetRegionsFilter {
  static readonly type = '[Genotype] Set regions filter';
  constructor(public regionsFilters: string[]) {}
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
  addEffectType(ctx: StateContext<RegionsFilterModel>, action: SetRegionsFilter) {
    ctx.patchState({
        regionsFilters: action.regionsFilters
    });
  }
}
