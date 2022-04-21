import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetFamilyTypeFilter {
  public static readonly type = '[Genotype] Set FamilyTypes';
  public constructor(public familyTypes: Set<string>) {}
}

export interface FamilyTypeFilterModel {
  familyTypes: string[];
}

@State<FamilyTypeFilterModel>({
  name: 'familyTypeFilterState',
  defaults: {
    familyTypes: ['trio', 'quad', 'multigenerational', 'simplex', 'multiplex', 'other']
  },
})
@Injectable()
export class FamilyTypeFilterState {
  @Action(SetFamilyTypeFilter)
  public setVariantTypes(ctx: StateContext<FamilyTypeFilterModel>, action: SetFamilyTypeFilter): void {
    ctx.patchState({
      familyTypes: [...action.familyTypes]
    });
  }
}
