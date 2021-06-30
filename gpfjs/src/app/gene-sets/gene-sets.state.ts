import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetGeneSetsValues {
  static readonly type = '[Genotype] Set geneSets values';
  constructor(public geneSetsValues: object) {}
}

export interface GeneSetsModel {
  geneSetsTypes: object;
  geneSetsCollection: object;
  geneSet: object;
}

@State<GeneSetsModel>({
  name: 'geneSetsState',
  defaults: {
    geneSetsTypes: {},
    geneSetsCollection: {},
    geneSet: {},
  },
})
@Injectable()
export class GeneSetsState {
  @Action(SetGeneSetsValues)
  setGeneSets(ctx: StateContext<GeneSetsModel>, action: SetGeneSetsValues) {
    ctx.patchState({
      geneSetsTypes: action.geneSetsValues['geneSetsTypes'],
      geneSetsCollection: action.geneSetsValues['geneSetsCollection'],
      geneSet: action.geneSetsValues['geneSet'],
    });
  }
}
