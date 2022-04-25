import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetPhenoToolMeasure {
  public static readonly type = '[Phenotype] Set phenoToolMeasure values';
  public constructor(public measureId: string, public normalizeBy: object[]) {}
}

export interface PhenoToolMeasureModel {
  measureId: string;
  normalizeBy: object[];
}

@State<PhenoToolMeasureModel>({
  name: 'phenoToolMeasureState',
  defaults: {
    measureId: '',
    normalizeBy: [],
  },
})
@Injectable()
export class PhenoToolMeasureState {
  @Action(SetPhenoToolMeasure)
  public setPhenoToolMeasure(ctx: StateContext<PhenoToolMeasureModel>, action: SetPhenoToolMeasure): void {
    ctx.patchState({
      measureId: action.measureId,
      normalizeBy: [...action.normalizeBy],
    });
  }
}
