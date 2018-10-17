import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

export class RolesFilter {
  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selected: Set<string> = new Set([
    // 'affected'
  ]);
}