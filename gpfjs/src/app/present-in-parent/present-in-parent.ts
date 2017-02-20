
export const PRESENT_IN_PARENT_CHECK = 'PRESENT_IN_PARENT_CHECK';
export const PRESENT_IN_PARENT_UNCHECK = 'PRESENT_IN_PARENT_UNCHECK';
export const PRESENT_IN_PARENT_CHECK_ALL = 'PRESENT_IN_PARENT_CHECK_ALL';
export const PRESENT_IN_PARENT_UNCHECK_ALL = 'PRESENT_IN_PARENT_UNCHECK_ALL';
export const PRESENT_IN_PARENT_RANGE_START_CHANGE = 'PRESENT_IN_PARENT_RANGE_START_CHANGE';
export const PRESENT_IN_PARENT_RANGE_END_CHANGE = 'PRESENT_IN_PARENT_RANGE_END_CHANGE';
export const PRESENT_IN_PARENT_ULTRA_RARE_CHANGE = 'PRESENT_IN_PARENT_ULTRA_RARE_CHANGE';

export interface PresentInParentState {
  motherOnly: boolean;
  fatherOnly: boolean;
  motherFather: boolean;
  neither: boolean;

  rarityIntervalStart: number;
  rarityIntervalEnd: number;
  ultraRare: boolean;
};

const initialState: PresentInParentState = {
  motherOnly: false,
  fatherOnly: false,
  motherFather: false,
  neither: true,

  rarityIntervalStart: 0,
  rarityIntervalEnd: 100,
  ultraRare: false
};

function resetInterval(state: PresentInParentState) {
  if (!state.motherOnly && !state.fatherOnly && !state.motherFather) {
    state.rarityIntervalStart = 0;
    state.rarityIntervalEnd = 100;
    state.ultraRare = false;
  }
  return state;
}

export function presentInParentReducer(
  state: PresentInParentState = initialState,
  action): PresentInParentState {


  switch (action.type) {
    case PRESENT_IN_PARENT_CHECK: {
      let newState = Object.assign({}, state,
        { [action.payload]: true });
      return resetInterval(newState);
    }
    case PRESENT_IN_PARENT_UNCHECK: {
      let newState = Object.assign({}, state,
        { [action.payload]: false });
      return resetInterval(newState);
    }
    case PRESENT_IN_PARENT_RANGE_START_CHANGE:
      return Object.assign({}, state,
        { rarityIntervalStart: action.payload });
    case PRESENT_IN_PARENT_RANGE_END_CHANGE:
      return Object.assign({}, state,
        { rarityIntervalEnd: action.payload });
    case PRESENT_IN_PARENT_ULTRA_RARE_CHANGE:
      return Object.assign({}, state,
        { ultraRare: action.payload });
    case PRESENT_IN_PARENT_CHECK_ALL: {
      let newStateAll = Object.assign({}, state,
        {
          motherOnly: true,
          fatherOnly: true,
          motherFather: true,
          neither: true
        });
      return resetInterval(newStateAll);
    }
    case PRESENT_IN_PARENT_UNCHECK_ALL: {
      let newStateAll = Object.assign({}, state,
        {
          motherOnly: false,
          fatherOnly: false,
          motherFather: false,
          neither: false
        });
      return resetInterval(newStateAll);
    }
    default:
      return state;
  }
};
