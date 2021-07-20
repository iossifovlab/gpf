import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetInheritanceTypes {
  static readonly type = '[Genotype] Set inheritanceType values';
  constructor(public inheritanceTypes: Set<string>) {}
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
  @Action(SetInheritanceTypes)
  setInheritanceTypes(ctx: StateContext<InheritancetypesModel>, action: SetInheritanceTypes) {
    ctx.patchState({
      inheritanceTypes: [...action.inheritanceTypes]
    });
  }
}
