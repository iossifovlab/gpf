import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { cloneDeep } from 'lodash';
export const initialState: { enrichmentBackgroundModel: string; enrichmentCountingModel: string} = {
  enrichmentBackgroundModel: '',
  enrichmentCountingModel: ''
};

export const selectEnrichmentModels =
  createFeatureSelector<{ enrichmentBackgroundModel: string; enrichmentCountingModel: string}>('enrichmentModels');

export const setEnrichmentModels = createAction(
  '[Genotype] Set enrichmentModel values',
  props<{ enrichmentBackgroundModel: string; enrichmentCountingModel: string }>()
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
