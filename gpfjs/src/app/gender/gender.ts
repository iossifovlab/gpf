
export const GENDER_CHECK = 'GENDER_CHECK';
export const GENDER_UNCHECK = 'GENDER_UNCHECK';
export const GENDER_CHECK_ALL = 'GENDER_CHECK_ALL';
export const GENDER_UNCHECK_ALL = 'GENDER_UNCHECK_ALL';

import { Equals, ValidateIf } from "class-validator";

export class GenderState {
  female: boolean;

  @ValidateIf(o => !o.female)
  @Equals(true, {
    message: "select at least one"
  })
  male: boolean;
};

const initialState: GenderState = {
  female: true,
  male: true
};

export function genderReducer(
  state: GenderState = initialState,
  action): GenderState {


  switch (action.type) {
    case GENDER_CHECK:
      return Object.assign({}, state,
        { [action.payload]: true });
    case GENDER_UNCHECK:
      return Object.assign({}, state,
        { [action.payload]: false });
    case GENDER_CHECK_ALL:
      return {
        female: true,
        male: true
      };
    case GENDER_UNCHECK_ALL:
      return {
        female: false,
        male: false
      };
    default:
      return state;
  }
};
