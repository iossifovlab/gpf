import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetVariantTypes {
  public static readonly type = '[Genotype] Set VariantType';
  public constructor(public variantTypes: Set<string>) {}
}

export interface VarianttypeModel {
  variantTypes: string[];
}

@State<VarianttypeModel>({
  name: 'varianttypesState',
  defaults: {
    variantTypes: []
  },
})
@Injectable()
export class VarianttypesState {
  @Action(SetVariantTypes)
  public setVariantTypes(ctx: StateContext<VarianttypeModel>, action: SetVariantTypes): void {
    ctx.patchState({
      variantTypes: [...action.variantTypes]
    });
  }
}
