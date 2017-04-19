import { IdDescription } from '../common/iddescription';
import { IsNotEmpty } from "class-validator";
import { ContinuousMeasure } from '../measures/measures'

export const PHENO_TOOL_MEASURE_CHANGE = 'PHENO_TOOL_MEASURE_CHANGE';
export const PHENO_TOOL_MEASURE_INIT = 'PHENO_TOOL_MEASURE_INIT'
export const PHENO_TOOL_NORMALIZE_BY_CHECK = 'PHENO_TOOL_NORMALIZE_BY_CHECK';
export const PHENO_TOOL_NORMALIZE_BY_UNCHECK = 'PHENO_TOOL_NORMALIZE_BY_UNCHECK';

export class PhenoToolMeasureState {
    @IsNotEmpty()
    measure: ContinuousMeasure;

    normalizeBy: string[];
};

const initialState: PhenoToolMeasureState = {
  measure: null,
  normalizeBy: []
};

export function phenoToolMeasureStateReducer(
  state: PhenoToolMeasureState = null,
  action): PhenoToolMeasureState {


  switch (action.type) {
    case PHENO_TOOL_MEASURE_CHANGE:
      return Object.assign({}, state,
        { measure: action.payload });
    case PHENO_TOOL_NORMALIZE_BY_CHECK:
      return Object.assign({}, state,
        { normalizeBy: [...state.normalizeBy.filter(et => et !== action.payload),
                    action.payload ]});
    case PHENO_TOOL_NORMALIZE_BY_UNCHECK:
      return Object.assign({}, state,
        { normalizeBy: state.normalizeBy.filter(et => et !== action.payload) });
    case PHENO_TOOL_MEASURE_INIT:
      return initialState;
    default:
      return state;
  }
};
