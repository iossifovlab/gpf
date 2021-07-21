import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetGeneSymbols {
  static readonly type = '[Genotype] Set gene symbols';
  constructor(public geneSymbols: string[]) {}
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
  setGeneSymbols(ctx: StateContext<GeneSymbolsModel>, action: SetGeneSymbols) {
    const state = ctx.getState();
    ctx.patchState({
      geneSymbols: action.geneSymbols
    });
  }
}
