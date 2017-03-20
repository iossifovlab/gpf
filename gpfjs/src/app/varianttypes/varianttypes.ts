import { ArrayNotEmpty } from "class-validator";

export class VariantTypesState {
  @ArrayNotEmpty({
    message: "select at least one"
  })
  selected: Array<string>;
}

const initialState: VariantTypesState = {
  selected: []
};


export const VARIANT_TYPES_CHECK = 'VARIANT_TYPES_CHECK';
export const VARIANT_TYPES_UNCHECK = 'VARIANT_TYPES_UNCHECK';
export const VARIANT_TYPES_SET = 'VARIANT_TYPES_SET';
export const VARIANT_TYPES_INIT = 'VARIANT_TYPES_INIT';


export function variantTypesReducer(
  state: VariantTypesState = null, action): VariantTypesState {
  switch (action.type) {
    case VARIANT_TYPES_CHECK:
      return Object.assign({}, state,
        { selected: [...state.selected.filter(et => et !== action.payload),
                    action.payload ]});
    case VARIANT_TYPES_UNCHECK:
      return Object.assign({}, state,
        { selected: state.selected.filter(et => et !== action.payload) });
    case VARIANT_TYPES_SET:
      return Object.assign({}, state,
        { selected: [...action.payload] });
    case VARIANT_TYPES_INIT:
      return initialState;
    default:
      return state;
  }
};
