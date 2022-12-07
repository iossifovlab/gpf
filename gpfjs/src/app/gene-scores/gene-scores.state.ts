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
  public setHistogramValues(ctx: StateContext<GeneScoresModel>, action: SetHistogramValues): void {
    ctx.patchState({
      rangeStart: action.rangeStart,
      rangeEnd: action.rangeEnd,
    });
  }

  @Action(SetGeneScore)
  public setGeneScore(ctx: StateContext<GeneScoresModel>, action: SetGeneScore): void {
    ctx.patchState({ geneScore: action.geneScore });
  }

  @Selector([GeneScoresState])
  public static queryStateSelector(geneScoresState: GeneScoresModel): object {
    if (geneScoresState.geneScore) {
      return {
        geneScores: {
          score: geneScoresState.geneScore['score'],
          rangeStart: geneScoresState.rangeStart,
          rangeEnd: geneScoresState.rangeEnd,
        }
      };
    }
    return null;
  }
}
