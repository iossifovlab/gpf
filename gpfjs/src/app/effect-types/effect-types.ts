export const ALL: Set<string> = new Set([
  '3\'UTR',
  '3\'UTR-intron',
  '5\'UTR',
  '5\'UTR-intron',
  'frame-shift',
  'intergenic',
  'intron',
  'missense',
  'no-frame-shift',
  'no-frame-shift-newStop',
  'noEnd',
  'noStart',
  'non-coding',
  'non-coding-intron',
  'nonsense',
  'splice-site',
  'synonymous',
  'CDS',
  'CNV+',
  'CNV-',
]);

export const CODING: Set<string> = new Set([
  'nonsense',
  'frame-shift',
  'splice-site',
  'no-frame-shift-newStop',
  'missense',
  'no-frame-shift',
  'noStart',
  'noEnd',
  'synonymous',
]);

export const NONCODING: Set<string> = new Set([
  'non-coding',
  'intron',
  'intergenic',
  '3\'UTR',
  '5\'UTR',
]);

export const CNV: Set<string> = new Set([
  'CNV+',
  'CNV-'
]);

export const LGDS: Set<string> = new Set([
  'frame-shift',
  'nonsense',
  'splice-site',
  'no-frame-shift-newStop',
]);

export const NONSYNONYMOUS: Set<string> = new Set([
  'nonsense',
  'frame-shift',
  'splice-site',
  'no-frame-shift-newStop',
  'missense',
  'no-frame-shift',
  'noStart',
  'noEnd',
]);

export const UTRS: Set<string> = new Set([
  '3\'UTR',
  '5\'UTR',
]);

export const OTHER: Set<string> = new Set([
  '3\'UTR',
  '3\'UTR-intron',
  '5\'UTR',
  '5\'UTR-intron',
  'intergenic',
  'intron',
  'no-frame-shift',
  'noEnd',
  'noStart',
  'non-coding',
  'non-coding-intron',
  'CDS',
]);

export const GENOTYPE_BROWSER_INITIAL_VALUES: Set<string> = new Set([
  'nonsense',
  'frame-shift',
  'splice-site',
  'no-frame-shift-newStop',
]);
