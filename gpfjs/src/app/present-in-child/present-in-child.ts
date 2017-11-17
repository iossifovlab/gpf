import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

export const ALL_STATES = new Set([
  'affected only',
  'unaffected only',
  'affected and unaffected',
  'neither'
]);

export class PresentInChild {
  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selected: Set<string> = new Set([
    'affected only',
    'affected and unaffected'
  ]);
}
