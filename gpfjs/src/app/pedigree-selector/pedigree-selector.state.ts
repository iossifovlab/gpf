import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPedigreeSelector {
  static readonly type = '[Genotype] Set pedigreeSelector';
  constructor(
    public id: string, public checkedValues: Set<string>,
  ) {}
}

export interface PedigreeSelectorModel {
  id: string;
  checkedValues: string[];
}

@State<PedigreeSelectorModel>({
  name: 'pedigreeSelectorState',
  defaults: <any>{},
})
@Injectable()
export class PedigreeSelectorState {
  @Action(SetPedigreeSelector)
  public setPedigreeSelector(ctx: StateContext<PedigreeSelectorModel>, action: SetPedigreeSelector) {
    ctx.patchState({
      id: action.id,
      checkedValues: [...action.checkedValues],
    });
  }
}
