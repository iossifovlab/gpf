import { Injectable } from '@angular/core';
import { State, Action, StateContext } from '@ngxs/store';

export class SetEnrichmentModels {
  static readonly type = '[Genotype] Set enrichmentModel values';
  constructor(
    public enrichmentBackgroundModel: string,
    public enrichmentCountingModel: string,
  ) {}
}

export interface EnrichmentModelsModel {
  enrichmentBackgroundModel: string,
  enrichmentCountingModel: string,
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
  setEnrichmentModels(ctx: StateContext<EnrichmentModelsModel>, action: SetEnrichmentModels) {
    ctx.patchState({
      enrichmentBackgroundModel: action.enrichmentBackgroundModel,
      enrichmentCountingModel: action.enrichmentCountingModel,
    });
  }
}
