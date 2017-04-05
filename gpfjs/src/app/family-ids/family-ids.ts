export const FAMILY_IDS_CHANGE = 'FAMILY_IDS_CHANGE';
export const FAMILY_IDS_INIT = 'FAMILY_IDS_INIT';

export class FamilyIdsState {
  familyIds: string;
};

const initialState: FamilyIdsState = {
  familyIds: ""
};

export function familyIdsReducer(
  state: FamilyIdsState = null,
  action): FamilyIdsState {


  switch (action.type) {
    case FAMILY_IDS_CHANGE:
      return Object.assign({}, state,
        { familyIds: action.payload });
    case FAMILY_IDS_INIT:
      return initialState;
    default:
      return state;
  }
};
