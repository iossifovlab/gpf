import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetUniqueFamilyVariantsFilter {
  public static readonly type = '[Genotype] Set Unique Family Variants Filter';
  public constructor(
    public uniqueFamilyVariants: boolean
  ) {}
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
  public setUniqueFamilyVariantsFilter(
    ctx: StateContext<UniqueFamilyVariantsFilterModel>,
    action: SetUniqueFamilyVariantsFilter
  ): void {
    ctx.patchState({ uniqueFamilyVariants: action.uniqueFamilyVariants });
  }
}
