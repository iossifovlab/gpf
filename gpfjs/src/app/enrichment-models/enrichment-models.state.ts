import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetEnrichmentModels {
  static readonly type = '[Genotype] Set enrichmentModel values';
  constructor(
    public enrichmentBackgroundModel: object,
    public enrichmentCountingModel: object,
  ) {}
}

export interface EnrichmentModelsModel {
  enrichmentBackgroundModel: object,
  enrichmentCountingModel: object,
}

@State<EnrichmentModelsModel>({
  name: 'enrichmentModelsState',
  defaults: {
    enrichmentBackgroundModel: {},
    enrichmentCountingModel: {},
  },
})
@Injectable()
export class EnrichmentModelsState {
  @Action(SetEnrichmentModels)
  setEnrichmentModels(ctx: StateContext<EnrichmentModelsModel>, action: SetEnrichmentModels) {
    ctx.patchState({
      enrichmentBackgroundModel: action.enrichmentBackgroundModel,
      enrichmentCountingModel: action.enrichmentCountingModel,
    });
  }
}
