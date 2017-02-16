
export const PRESENT_IN_CHILD_CHECK = 'PRESENT_IN_CHILD_CHECK';
export const PRESENT_IN_CHILD_UNCHECK = 'PRESENT_IN_CHILD_UNCHECK';
export const PRESENT_IN_CHILD_CHECK_ALL = 'PRESENT_IN_CHILD_CHECK_ALL';
export const PRESENT_IN_CHILD_UNCHECK_ALL = 'PRESENT_IN_CHILD_UNCHECK_ALL';


export interface PresentInChildState {
  autismOnly: boolean;
  unaffectedOnly: boolean;
  autismUnaffected: boolean;
  neither: boolean;
};

const initialState: PresentInChildState = {
  autismOnly: true,
  unaffectedOnly: false,
  autismUnaffected: true,
  neither: false
};

export function presentInChildReducer(
  state: PresentInChildState = initialState,
  action): PresentInChildState {


  switch (action.type) {
    case PRESENT_IN_CHILD_CHECK:
      return Object.assign({}, state,
        { [action.payload]: true });
    case PRESENT_IN_CHILD_UNCHECK:
      return Object.assign({}, state,
        { [action.payload]: false });
    case PRESENT_IN_CHILD_CHECK_ALL:
      return {
        autismOnly: true,
        unaffectedOnly: true,
        autismUnaffected: true,
        neither: true
      };
    case PRESENT_IN_CHILD_UNCHECK_ALL:
      return {
        autismOnly: false,
        unaffectedOnly: false,
        autismUnaffected: false,
        neither: false
      };
    default:
      return state;
  }
};
