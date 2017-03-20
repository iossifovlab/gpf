/**
 * New typescript file
 */
export const STUDY_TYPES_CHECK = 'STUDY_TYPES_CHECK';
export const STUDY_TYPES_UNCHECK = 'STUDY_TYPES_UNCHECK';
export const STUDY_TYPES_CHECK_ALL = 'STUDY_TYPES_CHECK_ALL';
export const STUDY_TYPES_UNCHECK_ALL = 'STUDY_TYPES_UNCHECK_ALL';
export const STUDY_TYPES_INIT = 'STUDY_TYPES_INIT';

import { Equals, ValidateIf } from "class-validator";


export class StudyTypesState {
  we: boolean;

  @ValidateIf(o => !o.we)
  @Equals(true, {
    message: "select at least one"
  })
  tg: boolean;
};

const initialState: StudyTypesState = {
  we: true,
  tg: true
};

export function studyTypesReducer(
  state: StudyTypesState = null,
  action): StudyTypesState {


  switch (action.type) {
    case STUDY_TYPES_CHECK:
      return Object.assign({}, state,
        { [action.payload]: true });
    case STUDY_TYPES_UNCHECK:
      return Object.assign({}, state,
        { [action.payload]: false });
    case STUDY_TYPES_CHECK_ALL:
      return {
        we: true,
        tg: true
      };
    case STUDY_TYPES_UNCHECK_ALL:
      return {
        we: false,
        tg: false
      };
    case STUDY_TYPES_INIT:
      return initialState;
    default:
      return null;
  }
};
