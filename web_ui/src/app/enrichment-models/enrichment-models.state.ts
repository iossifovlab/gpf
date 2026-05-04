import { createReducer, createAction, on, props, createFeatureSelector } from '@ngrx/store';
import { reset } from 'app/users/state-actions';
import { cloneDeep } from 'lodash';

export interface EnrichmentModelsState {
  enrichmentBackgroundModel: string;
  enrichmentCountingModel: string;
}

export const initialState: EnrichmentModelsState = {
  enrichmentBackgroundModel: '',
  enrichmentCountingModel: ''
};

export const selectEnrichmentModels =
  createFeatureSelector<EnrichmentModelsState>('enrichmentModels');

export const setEnrichmentModels = createAction(
  '[Genotype] Set enrichmentModel values',
  props<EnrichmentModelsState>()
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
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  on(reset, resetEnrichmentModels, state => cloneDeep(initialState)),
);
