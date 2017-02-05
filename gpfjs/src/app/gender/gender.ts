
export const GENDER_CHECK = 'GENDER_CHECK';
export const GENDER_UNCHECK = 'GENDER_UNCHECK';
export const GENDER_CHECK_ALL = 'GENDER_CHECK_ALL';
export const GENDER_UNCHECK_ALL = 'GENDER_UNCHECK_ALL';

// export type GenderState = Array<string>;

export interface GenderState {
  female: boolean;
  male: boolean;
};

const initialState: GenderState = {
  female: true,
  male: true
};

export function genderReducer(state: GenderState = initialState, action) {
  switch (action.type) {
    case GENDER_CHECK:
      return Object.assign({}, state,
        { [action.payload]: true });
    case GENDER_UNCHECK:
      return Object.assign({}, state,
        { [action.payload]: false });
    case GENDER_CHECK_ALL:
      return Object.assign({}, state,
        {
          female: true,
          male: true
        });
    case GENDER_UNCHECK_ALL:
      return Object.assign({}, state,
        {
          female: false,
          male: false
        });
    default:
      return state;
  }
};
