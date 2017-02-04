/**
 * New typescript file
 */

export const CHECK_EFFECT_TYPE = 'CHECK_EFFECT_TYPE';
export const UNCHECK_EFFECT_TYPE = 'UNCHECK_EFFECT_TYPE';

export const effectTypesReducer = (state: Array<string> = new Array<string>(), action) => {
  switch (action.type) {
    case CHECK_EFFECT_TYPE:
      if (state.indexOf(action.payload) !== -1) {
        return state;
      } else {
        return [...state, action.payload];
      }
    case UNCHECK_EFFECT_TYPE:
      if (state.indexOf(action.payload) === -1) {
        return state;
      } else {
        const index = state.indexOf(action.payload);
        return [
          ...state.slice(0, index - 1),
          ...state.slice(index + 1)
        ];
      }
    default:
      return state;
  }
};
