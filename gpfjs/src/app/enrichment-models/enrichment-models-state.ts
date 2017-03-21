import { IdDescription } from '../common/iddescription';
import { IsNotEmpty } from "class-validator";

export const ENRICHMENT_BACKGROUND_CHANGE = 'ENRICHMENT_BACKGROUND_CHANGE';
export const ENRICHMENT_COUNTING_CHANGE = 'ENRICHMENT_COUNTING_CHANGE';
export const ENRICHMENT_MODELS_INIT = 'ENRICHMENT_MODELS_INIT'


export class EnrichmentModelsState {
    @IsNotEmpty()
    background: IdDescription;

    @IsNotEmpty()
    counting: IdDescription;
};

const initialState: EnrichmentModelsState = {
  background: null,
  counting: null
};

export function enrichmentModelsReducer(
  state: EnrichmentModelsState = null,
  action): EnrichmentModelsState {


  switch (action.type) {
    case ENRICHMENT_BACKGROUND_CHANGE:
      return Object.assign({}, state,
        { background: action.payload });
    case ENRICHMENT_COUNTING_CHANGE:
      return Object.assign({}, state,
        { counting: action.payload });
    case ENRICHMENT_MODELS_INIT:
      return initialState;
    default:
      return state;
  }
};
