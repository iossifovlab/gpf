export const REGIONS_FILTER_CHANGE = 'REGIONS_FILTER_CHANGE';
export const REGIONS_FILTER_INIT = 'REGIONS_FILTER_INIT';
import { RegionsFilterValidator } from './regions-filter.validator'
import { Validate } from "class-validator";

export class RegionsFilterState {
  @Validate(RegionsFilterValidator)
  regionsFilter: string;
};

const initialState: RegionsFilterState = {
  regionsFilter: ""
};

export function regionsFilterReducer(
  state: RegionsFilterState = null,
  action): RegionsFilterState {


  switch (action.type) {
    case REGIONS_FILTER_CHANGE:
      return Object.assign({}, state,
        { regionsFilter: action.payload });
    case REGIONS_FILTER_INIT:
      return initialState;
    default:
      return state;
  }
};
