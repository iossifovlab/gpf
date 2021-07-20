import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetVariantTypes {
  static readonly type = '[Genotype] Set VariantType';
  constructor(public variantTypes: Set<string>) {}
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
  setVariantTypes(ctx: StateContext<VarianttypeModel>, action: SetVariantTypes) {
    ctx.patchState({
      variantTypes: [...action.variantTypes]
    });
  }
}
