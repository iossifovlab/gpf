
export const PRESENT_IN_CHILD_CHECK = 'PRESENT_IN_CHILD_CHECK';
export const PRESENT_IN_CHILD_UNCHECK = 'PRESENT_IN_CHILD_UNCHECK';
export const PRESENT_IN_CHILD_CHECK_ALL = 'PRESENT_IN_CHILD_CHECK_ALL';
export const PRESENT_IN_CHILD_UNCHECK_ALL = 'PRESENT_IN_CHILD_UNCHECK_ALL';


export type PresentInChildState = Array<string>;

//export interface PresentInChildState {
//  affectedOnly: boolean;
//  unaffectedOnly: boolean;
//  affectedUnaffected: boolean;
//  neither: boolean;
//};

//const initialState: PresentInChildState = {
//  affectedOnly: true,
//  unaffectedOnly: false,
//  affectedUnaffected: true,
//  neither: false
//};

const initialState: PresentInChildState = [
  'affected only',
  'affected and unaffected'
];

export function presentInChildReducer(
  state: PresentInChildState = initialState, action): PresentInChildState {


  switch (action.type) {
    case PRESENT_IN_CHILD_CHECK:
      return [
        ...state.filter(et => et !== action.payload),
        action.payload
      ];
    case PRESENT_IN_CHILD_UNCHECK:
      return state.filter(et => et !== action.payload);
    case PRESENT_IN_CHILD_CHECK_ALL:
      return [
        'affected only',
        'unaffected only',
        'affected and unaffected',
        'neither'
      ];
    case PRESENT_IN_CHILD_UNCHECK_ALL:
      return [];
    default:
      return state;
  }
};
