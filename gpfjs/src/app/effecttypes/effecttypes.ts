
export const CHECK_EFFECT_TYPE = 'CHECK_EFFECT_TYPE';
export const UNCHECK_EFFECT_TYPE = 'UNCHECK_EFFECT_TYPE';


export function effectTypesReducer(state: Array<string> = new Array<string>(), action): Array<string> {
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
