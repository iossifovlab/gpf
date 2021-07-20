import { Injectable } from '@angular/core';
import { State, Action, StateContext, Selector } from '@ngxs/store';

export class SetHistogramValues {
  static readonly type = '[Genotype] Set geneWeights histogram values';
  constructor(public rangeStart: number, public rangeEnd: number) {}
}

export class SetGeneWeight {
  static readonly type = '[Genotype] Set geneWeight';
  constructor(public geneWeight: object) {}
}

export interface GeneWeightsModel {
  geneWeight: object;
  rangeStart: number;
  rangeEnd: number;
}

@State<GeneWeightsModel>({
  name: 'geneWeightsState',
  defaults: {
    geneWeight: null,
    rangeStart: 0,
    rangeEnd: 0,
  },
})
@Injectable()
export class GeneWeightsState {
  @Action(SetHistogramValues)
  setHistogramValues(ctx: StateContext<GeneWeightsModel>, action: SetHistogramValues) {
    ctx.patchState({
      rangeStart: action.rangeStart,
      rangeEnd: action.rangeEnd,
    });
  }

  @Action(SetGeneWeight)
  setGeneWeight(ctx: StateContext<GeneWeightsModel>, action: SetGeneWeight) {
    ctx.patchState({ geneWeight: action.geneWeight });
  }

  @Selector([GeneWeightsState])
  static queryStateSelector(geneWeightsState: GeneWeightsModel) {
    if (geneWeightsState.geneWeight) {
      return {
        'weight': geneWeightsState.geneWeight['weight'],
        'rangeStart': geneWeightsState.rangeStart,
        'rangeEnd': geneWeightsState.rangeEnd,
      }
    }
    return null;
  }
}
