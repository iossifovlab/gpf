export const PHENO_TOOL_OTHERS: Set<string> = new Set([
  'Missense',
  'Nonsynonymous',
  'Synonymous',
]);

export const PHENO_TOOL_CNV: Set<string> = new Set([
  'CNV',
  'CNV+',
  'CNV-'
]);

export const PHENO_TOOL_LGDS: Set<string> = new Set([
  'LGDs',
  'Nonsense',
  'Frame-shift',
  'Splice-site',
]);

export const PHENO_TOOL_INITIAL_VALUES: Set<string> = new Set([
  'LGDs',
  'Missense',
  'Synonymous',
]);

export const PHENO_TOOL_ALL: Set<string> = new Set([...PHENO_TOOL_OTHERS, ...PHENO_TOOL_CNV, ...PHENO_TOOL_LGDS]);
