import { ArrayNotEmpty } from 'class-validator';

export class EffectTypes {
  @ArrayNotEmpty({
    message: 'select at least one'
  })
  selected: Array<string> = [];
}

export const ALL: string[] = [
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'No-frame-shift-newStop',
  'Missense',
  'No-frame-shift',
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
  'No-frame-shift-newStop',
  'Missense',
  'No-frame-shift',
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
  'No-frame-shift-newStop',
];

export const NONSYNONYMOUS: string[] = [
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'No-frame-shift-newStop',
  'Missense',
  'No-frame-shift',
  'noStart',
  'noEnd',
];

export const UTRS: string[] = [
  '3\'-UTR',
  '5\'-UTR',
];
