import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetGeneSymbols {
  public static readonly type = '[Genotype] Set gene symbols';
  public constructor(public geneSymbols: string[]) {}
}

export interface GeneSymbolsModel {
  geneSymbols: string[];
}

@State<GeneSymbolsModel>({
  name: 'geneSymbolsState',
  defaults: {
    geneSymbols: []
  },
})
@Injectable()
export class GeneSymbolsState {
  @Action(SetGeneSymbols)
  public setGeneSymbols(ctx: StateContext<GeneSymbolsModel>, action: SetGeneSymbols): void {
    ctx.patchState({
      geneSymbols: action.geneSymbols
    });
  }
}
