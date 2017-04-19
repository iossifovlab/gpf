export const PHENO_TOOL_OTHERS: string[] = [
  'Missense',
  'Nonsynonymous',
  'Synonymous',
];

export const PHENO_TOOL_CNV: string[] = [
  'CNV',
  'CNV+',
  'CNV-'
];

export const PHENO_TOOL_LGDS: string[] = [
  'LGDs',
  'Nonsense',
  'Frame-shift',
  'Splice-site',
];

export const PHENO_TOOL_INITIAL_VALUES: string[] = [
  'LGDs',
  'Missense',
  'Synonymous',
  'CNV',
];

export const PHENO_TOOL_ALL: string[] =
  PHENO_TOOL_OTHERS.concat(PHENO_TOOL_CNV).concat(PHENO_TOOL_LGDS)
