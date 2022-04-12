import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetUniqueFamilyVariantsFilter {
  static readonly type = '[Genotype] Set Unique Family Variants Filter';
  constructor(public uniqueFamilyVariants: boolean) {}
}

export interface UniqueFamilyVariantsFilterModel {
  uniqueFamilyVariants: boolean;
}

@State<UniqueFamilyVariantsFilterModel >({
  name: 'uniqueFamilyVariantsFilterState',
  defaults: { uniqueFamilyVariants: false },
})
@Injectable()
export class UniqueFamilyVariantsFilterState {
  @Action(SetUniqueFamilyVariantsFilter)
  setUniqueFamilyVariantsFilter(ctx: StateContext<UniqueFamilyVariantsFilterModel>, action: SetUniqueFamilyVariantsFilter) {
    ctx.patchState({ uniqueFamilyVariants: action.uniqueFamilyVariants });
  }
}
