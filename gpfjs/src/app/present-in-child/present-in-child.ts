
export const PRESENT_IN_CHILD_CHECK = 'PRESENT_IN_CHILD_CHECK';
export const PRESENT_IN_CHILD_UNCHECK = 'PRESENT_IN_CHILD_UNCHECK';
export const PRESENT_IN_CHILD_CHECK_ALL = 'PRESENT_IN_CHILD_CHECK_ALL';
export const PRESENT_IN_CHILD_UNCHECK_ALL = 'PRESENT_IN_CHILD_UNCHECK_ALL';
export const PRESENT_IN_CHILD_INIT = 'PRESENT_IN_CHILD_INIT';
export const PRESENT_IN_CHILD_SET = 'PRESENT_IN_CHILD_SET';

import { ArrayNotEmpty } from "class-validator"

export class PresentInChildState {
  @ArrayNotEmpty({
    message: "select at least one"
  })
  selected: Array<string>;
}

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

const initialState: PresentInChildState = {
  selected : [
    'affected only',
    'affected and unaffected'
  ]
};

export function presentInChildReducer(
  state: PresentInChildState = null, action): PresentInChildState {


  switch (action.type) {
    case PRESENT_IN_CHILD_CHECK:
      return Object.assign({}, state,
        { selected: [...state.selected.filter(et => et !== action.payload),
                    action.payload ]});
    case PRESENT_IN_CHILD_UNCHECK:
      return Object.assign({}, state,
        { selected: state.selected.filter(et => et !== action.payload) });
    case PRESENT_IN_CHILD_CHECK_ALL:
    return Object.assign({}, state,
      { selected: [
        'affected only',
        'unaffected only',
        'affected and unaffected',
        'neither'
      ]});
    case PRESENT_IN_CHILD_UNCHECK_ALL:
      return Object.assign({}, state,
        { selected: [] });
    case PRESENT_IN_CHILD_SET:
      return Object.assign({}, state,
        { selected: action.payload });
    case PRESENT_IN_CHILD_INIT:
      return initialState;
    default:
      return state;
  }
};
