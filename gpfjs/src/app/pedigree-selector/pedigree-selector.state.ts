import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPedigreeSelector {
  static readonly type = '[Genotype] Set pedigreeSelector';
  constructor(
    public id: string, public selectedValues: Set<string>,
  ) {}
}

export interface PedigreeSelectorModel {
  id: string;
  selectedValues: string[];
}

@State<PedigreeSelectorModel>({
  name: 'pedigreeSelectorState',
  defaults: {
    id: '',
    selectedValues: [],
  },
})
@Injectable()
export class PedigreeSelectorState {
  @Action(SetPedigreeSelector)
  setInheritanceTypes(ctx: StateContext<PedigreeSelectorModel>, action: SetPedigreeSelector) {
    ctx.patchState({
      id: action.id,
      selectedValues: [...action.selectedValues],
    });
  }
}
