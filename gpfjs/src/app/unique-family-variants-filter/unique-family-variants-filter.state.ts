import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetUniqueFamilyVariantsFilter {
  static readonly type = '[Genotype] Set Unique Family Variants Filter';
  constructor(public uniqueFamilyVariantsFilter: boolean) {}
}

export interface UniqueFamilyVariantsFilterModel {
  uniqueFamilyVariantsFilter: boolean;
}

@State<UniqueFamilyVariantsFilterModel >({
  name: 'uniqueFamilyVariantsFilterState',
  defaults: { uniqueFamilyVariantsFilter: false },
})
@Injectable()
export class UniqueFamilyVariantsFilterState {
  @Action(SetUniqueFamilyVariantsFilter)
  setUniqueFamilyVariantsFilter(ctx: StateContext<UniqueFamilyVariantsFilterModel>, action: SetUniqueFamilyVariantsFilter) {
    ctx.patchState({ uniqueFamilyVariantsFilter: action.uniqueFamilyVariantsFilter });
  }
}
