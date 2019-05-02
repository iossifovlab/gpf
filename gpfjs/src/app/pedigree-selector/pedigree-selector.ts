import { Validate } from 'class-validator';

import { PedigreeSelector } from '../datasets/datasets';
import { SetNotEmpty } from '../utils/set.validators';

export class PedigreeSelectorState {
  pedigree: PedigreeSelector = null;

  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  checkedValues = new Set();
}
