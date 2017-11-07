
export const PRESENT_IN_PARENT_CHECK = 'PRESENT_IN_PARENT_CHECK';
export const PRESENT_IN_PARENT_UNCHECK = 'PRESENT_IN_PARENT_UNCHECK';
export const PRESENT_IN_PARENT_CHECK_ALL = 'PRESENT_IN_PARENT_CHECK_ALL';
export const PRESENT_IN_PARENT_UNCHECK_ALL = 'PRESENT_IN_PARENT_UNCHECK_ALL';
export const PRESENT_IN_PARENT_RANGE_START_CHANGE = 'PRESENT_IN_PARENT_RANGE_START_CHANGE';
export const PRESENT_IN_PARENT_RANGE_END_CHANGE = 'PRESENT_IN_PARENT_RANGE_END_CHANGE';
export const PRESENT_IN_PARENT_ULTRA_RARE_CHANGE = 'PRESENT_IN_PARENT_ULTRA_RARE_CHANGE';
export const PRESENT_IN_PARENT_INIT = 'PRESENT_IN_PARENT_INIT';
export const PRESENT_IN_PARENT_RARITY_TYPE_CHANGE = 'PRESENT_IN_PARENT_RARITY_TYPE_CHANGE';

export const RARITY_ULTRARARE = 'ultraRare';
export const RARITY_INTERVAL = 'interval';
export const RARITY_RARE = 'rare';
export const RARITY_ALL = 'all';



import { Equals, ValidateIf, Min, Max } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class PresentInParentState {
  @ValidateIf(o => !o.fatherOnly && !o.motherFather && !o.neither)
  @Equals(true, {
    message: 'select at least one'
  })
  motherOnly: boolean;

  fatherOnly: boolean;
  motherFather: boolean;
  neither: boolean;

  @ValidateIf(o => !o.ultraRare)
  @Min(0)
  @Max(100)
  @IsLessThanOrEqual('rarityIntervalEnd')
  rarityIntervalStart: number;


  @ValidateIf(o => !o.ultraRare)
  @Min(0)
  @Max(100)
  @IsMoreThanOrEqual('rarityIntervalEnd')
  rarityIntervalEnd: number;

  rarityType: string;

  ultraRare: boolean;
};

const initialState: PresentInParentState = {
  motherOnly: false,
  fatherOnly: false,
  motherFather: false,
  neither: true,

  rarityType: RARITY_ULTRARARE,
  rarityIntervalStart: 0,
  rarityIntervalEnd: 100,
  ultraRare: true
};

function resetInterval(state: PresentInParentState) {
  if (!state.motherOnly && !state.fatherOnly && !state.motherFather) {
    state.rarityIntervalStart = 0;
    state.rarityIntervalEnd = 100;
    state.ultraRare = true;
    state.rarityType = RARITY_ULTRARARE;
  }
  return state;
}

export function presentInParentReducer(
  state: PresentInParentState = null,
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
        {
          ultraRare: action.payload,
          rarityType: action.payload ? RARITY_ULTRARARE : state.rarityType
        });
    case PRESENT_IN_PARENT_RARITY_TYPE_CHANGE:
      return Object.assign({}, state,
        { rarityType: action.payload });
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
    case PRESENT_IN_PARENT_INIT:
      return initialState;
    default:
      return state;
  }
};
