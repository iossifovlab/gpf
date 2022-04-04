import { Injectable } from '@angular/core';
import { State, Action, StateContext, Selector } from '@ngxs/store';

export class SetHistogramValues {
  static readonly type = '[Genotype] Set geneScores histogram values';
  constructor(public rangeStart: number, public rangeEnd: number) {}
}

export class SetGeneScore {
  static readonly type = '[Genotype] Set geneScore';
  constructor(public geneScore: object) {}
}

export interface GeneScoresModel {
  geneScore: object;
  rangeStart: number;
  rangeEnd: number;
}

@State<GeneScoresModel>({
  name: 'geneScoresState',
  defaults: {
    geneScore: null,
    rangeStart: 0,
    rangeEnd: 0,
  },
})
@Injectable()
export class GeneScoresState {
  @Action(SetHistogramValues)
  setHistogramValues(ctx: StateContext<GeneScoresModel>, action: SetHistogramValues) {
    ctx.patchState({
      rangeStart: action.rangeStart,
      rangeEnd: action.rangeEnd,
    });
  }

  @Action(SetGeneScore)
  setGeneScore(ctx: StateContext<GeneScoresModel>, action: SetGeneScore) {
    ctx.patchState({ geneScore: action.geneScore });
  }

  @Selector([GeneScoresState])
  static queryStateSelector(geneScoresState: GeneScoresModel) {
    if (geneScoresState.geneScore) {
      return {
        geneScores: {
          'score': geneScoresState.geneScore['score'],
          'rangeStart': geneScoresState.rangeStart,
          'rangeEnd': geneScoresState.rangeEnd,
        }
      }
    }
    return null;
  }
}
