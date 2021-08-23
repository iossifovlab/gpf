import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

export class EffectTypes {
  @Validate(SetNotEmpty, {message: 'select at least one'})
  public selected: Set<string> = new Set();
}

export const ALL: Set<string> = new Set([
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
]);

export const CODING: Set<string> = new Set([
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'No-frame-shift-newStop',
  'Missense',
  'No-frame-shift',
  'noStart',
  'noEnd',
  'Synonymous',
]);

export const NONCODING: Set<string> = new Set([
  'Non coding',
  'Intron',
  'Intergenic',
  '3\'-UTR',
  '5\'-UTR',
]);

export const CNV: Set<string> = new Set([
  'CNV+',
  'CNV-'
]);

export const LGDS: Set<string> = new Set([
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'No-frame-shift-newStop',
]);

export const NONSYNONYMOUS: Set<string> = new Set([
  'Nonsense',
  'Frame-shift',
  'Splice-site',
  'No-frame-shift-newStop',
  'Missense',
  'No-frame-shift',
  'noStart',
  'noEnd',
]);

export const UTRS: Set<string> = new Set([
  '3\'-UTR',
  '5\'-UTR',
]);
