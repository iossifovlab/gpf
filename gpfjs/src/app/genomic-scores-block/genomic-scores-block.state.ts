import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetGenomicScores {
  static readonly type = '[Genotype] Set genomicScores values';
  constructor(public genomicScores: object[]) {}
}

export interface GenomicScoresBlockModel {
  genomicScores: object[];
}

@State<GenomicScoresBlockModel>({
  name: 'genomicScoresBlockState',
  defaults: {
    genomicScores: []
  },
})
@Injectable()
export class GenomicScoresBlockState {
  @Action(SetGenomicScores)
  setGenomicScores(ctx: StateContext<GenomicScoresBlockModel>, action: SetGenomicScores) {
    ctx.patchState({
      genomicScores: [...action.genomicScores]
    });
  }
}
