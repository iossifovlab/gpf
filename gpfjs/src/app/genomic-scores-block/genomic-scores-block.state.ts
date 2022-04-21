import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetGenomicScores {
  public static readonly type = '[Genotype] Set genomicScores values';
  public constructor(
    public genomicScores: object[]
  ) {}
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
  public setGenomicScores(ctx: StateContext<GenomicScoresBlockModel>, action: SetGenomicScores): void {
    ctx.patchState({
      genomicScores: [...action.genomicScores]
    });
  }
}
