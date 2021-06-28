import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddVariantType {
  static readonly type = '[Genotype] Add VariantType';
  constructor(public variantType: string) {}
}

export class RemoveVariantType {
  static readonly type = '[Genotype] Remove VariantType';
  constructor(public variantType: string) {}
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
  @Action(AddVariantType)
  addVariantType(ctx: StateContext<VarianttypeModel>, action: AddVariantType) {
    const state = ctx.getState();
    ctx.patchState({
      variantTypes: [...state.variantTypes, action.variantType]
    });
  }

  @Action(RemoveVariantType)
  removeVariantType(ctx: StateContext<VarianttypeModel>, action: RemoveVariantType) {
    const state = ctx.getState();
    ctx.patchState({
      variantTypes: state.variantTypes.filter(variantType => variantType !== action.variantType)
    });
  }
}
