import { Injectable } from '@angular/core';
import { State, Action, StateContext, Selector } from '@ngxs/store';

export class SetGeneSetsValues {
  public static readonly type = '[Genotype] Set geneSets values';
  public constructor(public geneSetsValues: object) {}
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
  @Selector([GeneSetsState])
  public static queryStateSelector(geneSetsState: GeneSetsModel): object {
    if (geneSetsState.geneSet) {
      return {
        geneSet: {
          geneSet: geneSetsState.geneSet['name'],
          geneSetsCollection: geneSetsState.geneSetsCollection['name'],
          geneSetsTypes: geneSetsState.geneSetsTypes,
        }
      };
    }
    return null;
  }

  @Action(SetGeneSetsValues)
  public setGeneSets(ctx: StateContext<GeneSetsModel>, action: SetGeneSetsValues): void {
    ctx.patchState({
      geneSetsTypes: action.geneSetsValues['geneSetsTypes'],
      geneSetsCollection: action.geneSetsValues['geneSetsCollection'],
      geneSet: action.geneSetsValues['geneSet'],
    });
  }
}
