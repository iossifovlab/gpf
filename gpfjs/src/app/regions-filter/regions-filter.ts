export const REGIONS_FILTER_CHANGE = 'REGIONS_FILTER_CHANGE';


export interface RegionsFilterState {
  regionsFilter: string;
};

const initialState: RegionsFilterState = {
  regionsFilter: ""
};

export function regionsFilterReducer(
  state: RegionsFilterState = initialState,
  action): RegionsFilterState {


  switch (action.type) {
    case REGIONS_FILTER_CHANGE:
      return Object.assign({}, state,
        { regionsFilter: action.payload });
    default:
      return state;
  }
};
