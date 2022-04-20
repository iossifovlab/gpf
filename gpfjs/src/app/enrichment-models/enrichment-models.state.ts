import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetEnrichmentModels {
  public static readonly type = '[Genotype] Set enrichmentModel values';
  public constructor(
    public enrichmentBackgroundModel: string,
    public enrichmentCountingModel: string,
  ) {}
}

export interface EnrichmentModelsModel {
  enrichmentBackgroundModel: string;
  enrichmentCountingModel: string;
}

@State<EnrichmentModelsModel>({
  name: 'enrichmentModelsState',
  defaults: {
    enrichmentBackgroundModel: '',
    enrichmentCountingModel: '',
  },
})
@Injectable()
export class EnrichmentModelsState {
  @Action(SetEnrichmentModels)
  public setEnrichmentModels(ctx: StateContext<EnrichmentModelsModel>, action: SetEnrichmentModels): void {
    ctx.patchState({
      enrichmentBackgroundModel: action.enrichmentBackgroundModel,
      enrichmentCountingModel: action.enrichmentCountingModel,
    });
  }
}
