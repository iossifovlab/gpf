/**
 * New typescript file
 */
export const STUDY_TYPES_CHECK = 'STUDY_TYPES_CHECK';
export const STUDY_TYPES_UNCHECK = 'STUDY_TYPES_UNCHECK';
export const STUDY_TYPES_CHECK_ALL = 'STUDY_TYPES_CHECK_ALL';
export const STUDY_TYPES_UNCHECK_ALL = 'STUDY_TYPES_UNCHECK_ALL';


export interface StudyTypesState {
  we: boolean;
  tg: boolean;
};

const initialState: StudyTypesState = {
  we: true,
  tg: true
};

export function studyTypesReducer(
  state: StudyTypesState = initialState,
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
    default:
      return state;
  }
};
