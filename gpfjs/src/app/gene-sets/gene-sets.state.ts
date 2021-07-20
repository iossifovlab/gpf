import { Injectable } from '@angular/core';
import { State, Action, StateContext, Selector } from '@ngxs/store';

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
    geneSetsTypes: null,
    geneSetsCollection: null,
    geneSet: null,
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

  @Selector([GeneSetsState])
  static queryStateSelector(geneSetsState: GeneSetsModel) {
    if (geneSetsState.geneSet) {
      return {
        'geneSet': geneSetsState.geneSet['name'],
        'geneSetsCollection': geneSetsState.geneSetsCollection['name'],
        'geneSetsTypes': geneSetsState.geneSetsTypes,
      }
    }
    return null;
  }
}
