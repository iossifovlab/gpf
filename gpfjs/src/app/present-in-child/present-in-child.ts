import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

export const ALL_STATES = new Set([
  'proband only',
  'sibling only',
  'proband and sibling',
  'neither'
]);

export class PresentInChild {
  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selected: Set<string> = new Set([
    'proband only',
    'proband and sibling'
  ]);
}
