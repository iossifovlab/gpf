import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';

export interface EnrichmentModels {
  enrichmentBackgroundModel: string;
  enrichmentCountingModel: string;
}

export const initialState: EnrichmentModels = {
  enrichmentBackgroundModel: '',
  enrichmentCountingModel: ''
};

export const selectEnrichmentModels =
  createFeatureSelector<EnrichmentModels>('enrichmentModels');

export const setEnrichmentModels = createAction(
  '[Genotype] Set enrichmentModel values',
  props<EnrichmentModels>()
);

export const resetEnrichmentModels = createAction(
  '[Genotype] Reset enrichmentModel values'
);

export const enrichmentModelsReducer = createReducer(
  initialState,
  on(setEnrichmentModels, (state, {enrichmentBackgroundModel, enrichmentCountingModel}) => ({
    enrichmentBackgroundModel: enrichmentBackgroundModel,
    enrichmentCountingModel: enrichmentCountingModel,
  })),
  on(resetEnrichmentModels, state => cloneDeep(initialState)),
);
