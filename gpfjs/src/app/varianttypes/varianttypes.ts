
export interface VariantTypesState {
  sub: boolean;
  ins: boolean;
  del: boolean;
  cnv: boolean;
};

const initialState: VariantTypesState = {
  sub: true,
  ins: true,
  del: true,
  cnv: true,
};

export const VARIANT_TYPES_CHECK = 'VARIANT_TYPES_CHECK';
export const VARIANT_TYPES_UNCHECK = 'VARIANT_TYPES_UNCHECK';
export const VARIANT_TYPES_CHECK_ALL = 'VARIANT_TYPES_CHECK_ALL';
export const VARIANT_TYPES_UNCHECK_ALL = 'VARIANT_TYPES_UNCHECK_ALL';


export function variantTypesReducer(
  state: VariantTypesState = initialState,
  action): VariantTypesState {

  switch (action.type) {
    case VARIANT_TYPES_CHECK:
      return Object.assign({}, state,
        { [action.payload]: true });
    case VARIANT_TYPES_UNCHECK:
      return Object.assign({}, state,
        { [action.payload]: false });
    case VARIANT_TYPES_CHECK_ALL:
      return {
        sub: true,
        ins: true,
        del: true,
        cnv: true,
      };
    case VARIANT_TYPES_UNCHECK_ALL:
      return {
        sub: false,
        ins: false,
        del: false,
        cnv: true,
      };
    default:
      return state;
  }
};
