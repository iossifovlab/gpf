
export const EFFECT_TYPE_CHECK = 'EFFECT_TYPE_CHECK';
export const EFFECT_TYPE_UNCHECK = 'EFFECT_TYPE_UNCHECK';
export const EFFECT_TYPE_SET = 'EFFECT_TYPE_SET';
export const EFFECT_TYPE_INIT = 'EFFECT_TYPE_INIT';

import { ArrayNotEmpty } from "class-validator"

export class EffectTypesState {
  @ArrayNotEmpty({
    message: "select at least one"
  })
  selected: Array<string>;
}

const initialState: EffectTypesState = {
  selected: []
};

export function effectTypesReducer(
  state: EffectTypesState = null, action): EffectTypesState {
  switch (action.type) {
    case EFFECT_TYPE_CHECK:
      return Object.assign({}, state,
        { selected: [...state.selected.filter(et => et !== action.payload),
                    action.payload ]});
    case EFFECT_TYPE_UNCHECK:
      return Object.assign({}, state,
        { selected: state.selected.filter(et => et !== action.payload) });
    case EFFECT_TYPE_SET:
      return Object.assign({}, state,
        { selected: [...action.payload] });
    case EFFECT_TYPE_INIT:
      return initialState;
    default:
      return state;
  }
};


export const ALL: string[] = [
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'Missense',
  'Non-frame-shift',
  'noStart',
  'noEnd',
  'Synonymous',
  'Non coding',
  'Intron',
  'Intergenic',
  '3\'-UTR',
  '5\'-UTR',
  'CNV+',
  'CNV-'
];

export const CODING: string[] = [
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'Missense',
  'Non-frame-shift',
  'noStart',
  'noEnd',
  'Synonymous',
];

export const NONCODING: string[] = [
  'Non coding',
  'Intron',
  'Intergenic',
  '3\'-UTR',
  '5\'-UTR',
];

export const CNV: string[] = [
  'CNV+',
  'CNV-'
];

export const LGDS: string[] = [
  'Nonsense',
  'Frame-shift',
  'Splice-site',
];

export const NONSYNONYMOUS: string[] = [
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'Missense',
  'Non-frame-shift',
  'noStart',
  'noEnd',
];

export const UTRS: string[] = [
  '3\'-UTR',
  '5\'-UTR',
];
