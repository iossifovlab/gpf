import { ENRICHMENT_MODELS_TAB_DESELECT } from '../store/common';
import { IdDescription } from '../common/iddescription';

export const ENRICHMENT_BACKGROUND_CHANGE = 'ENRICHMENT_BACKGROUND_CHANGE';
export const ENRICHMENT_COUNTING_CHANGE = 'ENRICHMENT_COUNTING_CHANGE';



export interface EnrichmentModelsState {
    background: IdDescription,
    counting: IdDescription
};

const initialState: EnrichmentModelsState = {
  background: null,
  counting: null
};

export function enrichmentModelsReducer(
  state: EnrichmentModelsState = initialState,
  action): EnrichmentModelsState {


  switch (action.type) {
    case ENRICHMENT_BACKGROUND_CHANGE:
      return Object.assign({}, state,
        { background: action.payload });
    case ENRICHMENT_COUNTING_CHANGE:
      return Object.assign({}, state,
        { counting: action.payload });
    case ENRICHMENT_MODELS_TAB_DESELECT:
      return initialState;
    default:
      return state;
  }
};
