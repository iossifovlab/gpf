import { PedigreeSelector } from '../datasets/datasets';
import { ArrayNotEmpty } from "class-validator"

export class PedigreeSelectorState {
  pedigree: PedigreeSelector;

  @ArrayNotEmpty({
    message: "select at least one"
  })
  checkedValues: string[];
};

const initialState = {
  pedigree: undefined,
  checkedValues: []
};

export const PEDIGREE_SELECTOR_INIT = 'PEDIGREE_SELECTOR_INIT';
export const PEDIGREE_SELECTOR_CHECK_VALUE = 'PEDIGREE_SELECTOR_CHECK_VALUE';
export const PEDIGREE_SELECTOR_UNCHECK_VALUE = 'PEDIGREE_SELECTOR_UNCHECK_VALUE';
export const PEDIGREE_SELECTOR_SET_CHECKED_VALUES = 'PEDIGREE_SELECTOR_SET_CHECKED_VALUES';


export function pedigreeSelectorReducer(
  state: PedigreeSelectorState = null, action) {

  switch (action.type) {
    case PEDIGREE_SELECTOR_INIT:
      return {
        pedigree: action.payload,
        checkedValues: action.payload.domain.map(sv => sv.id)
      };
    case PEDIGREE_SELECTOR_CHECK_VALUE:
      if (state.checkedValues.indexOf(action.payload) !== -1) {
        return state;
      } else {
        return {
          pedigree: state.pedigree,
          checkedValues: [...state.checkedValues, action.payload],
        };
      }
    case PEDIGREE_SELECTOR_UNCHECK_VALUE:
      return {
        pedigree: state.pedigree,
        checkedValues: state.checkedValues.filter(v => v !== action.payload),
      };

    case PEDIGREE_SELECTOR_SET_CHECKED_VALUES:
      return {
        pedigree: state.pedigree,
        checkedValues: [...action.payload]
      };
    default:
      return state;

  }
};
