
export const EFFECT_TYPE_CHECK = 'EFFECT_TYPE_CHECK';
export const EFFECT_TYPE_UNCHECK = 'EFFECT_TYPE_UNCHECK';
export const EFFECT_TYPE_SET = 'EFFECT_TYPE_SET';


export type EffectTypesState = Array<string>;

export function effectTypesReducer(
  state: EffectTypesState = [], action): EffectTypesState {
  switch (action.type) {
    case EFFECT_TYPE_CHECK:
      return [
        ...state.filter(et => et !== action.payload),
        action.payload
      ];
    case EFFECT_TYPE_UNCHECK:
      return state.filter(et => et !== action.payload);
    case EFFECT_TYPE_SET:
      return [...action.payload];
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
