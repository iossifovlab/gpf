
export const CHECK_GENDER = 'CHECK_GENDER';
export const UNCHECK_GENDER = 'UNCHECK_GENDER';


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
