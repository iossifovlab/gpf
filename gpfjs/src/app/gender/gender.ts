
export const CHECK_GENDER = 'GENDER_CHECK';
export const UNCHECK_GENDER = 'GENDER_UNCHECK';


export function genderReducer(state: Array<string> = new Array<string>(), action) {
  switch (action.type) {
    case CHECK_GENDER:
      if (state) {
        return state;
      }
    default:
      return state
  }
};
