import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

export const ALL_STATES = new Set([
  'affected',
  'unaffected',
  'affected and unaffected',
]);

export class StatusFilter {
  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selected: Set<string> = new Set([
    'affected'
  ]);
}
