import { IdDescription } from '../common/iddescription';
import { IsNotEmpty } from "class-validator";
import { ContinuousMeasure } from '../measures/measures'

export const PHENO_TOOL_MEASURE_CHANGE = 'PHENO_TOOL_MEASURE_CHANGE';
export const PHENO_TOOL_MEASURE_INIT = 'PHENO_TOOL_MEASURE_INIT'


export class PhenoToolMeasureState {
    @IsNotEmpty()
    measure: ContinuousMeasure;
};

const initialState: PhenoToolMeasureState = {
  measure: null
};

export function phenoToolMeasureStateReducer(
  state: PhenoToolMeasureState = null,
  action): PhenoToolMeasureState {


  switch (action.type) {
    case PHENO_TOOL_MEASURE_CHANGE:
      return Object.assign({}, state,
        { measure: action.payload });
    case PHENO_TOOL_MEASURE_INIT:
      return initialState;
    default:
      return state;
  }
};
