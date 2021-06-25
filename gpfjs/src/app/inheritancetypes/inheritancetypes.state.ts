import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class AddInheritanceType {
  static readonly type = '[Genotype] Add inheritance type';
  constructor(public inheritanceType: string) {}
}

export class RemoveInheritanceType {
  static readonly type = '[Genotype] Remove inheritance type';
  constructor(public inheritanceType: string) {}
}

export interface InheritancetypesModel {
  inheritanceTypes: string[];
}

@State<InheritancetypesModel>({
  name: 'inheritancetypesState',
  defaults: {
    inheritanceTypes: []
  },
})
@Injectable()
export class InheritancetypesState {
  @Action(AddInheritanceType)
  addInheritanceType(ctx: StateContext<InheritancetypesModel>, action: AddInheritanceType) {
    const state = ctx.getState();
    ctx.patchState({
      inheritanceTypes: [...state.inheritanceTypes, action.inheritanceType]
    });
  }

  @Action(RemoveInheritanceType)
  removeInheritanceType(ctx: StateContext<InheritancetypesModel>, action: RemoveInheritanceType) {
    const state = ctx.getState();
    ctx.patchState({
      inheritanceTypes: state.inheritanceTypes.filter(inh => inh !== action.inheritanceType)
    });
  }
}
