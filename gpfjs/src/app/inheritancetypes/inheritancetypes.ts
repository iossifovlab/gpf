import { Validate } from 'class-validator';
import { SetNotEmpty } from '../utils/set.validators';

export const inheritanceTypeDisplayNames = {
 'reference': 'Reference',
 'mendelian': 'Mendelian',
 'denovo': 'Denovo',
 'possible_denovo': 'Possible denovo',
 'omission': 'Omission',
 'possible_omission': 'Possible omission',
 'other': 'Other',
 'missing': 'Missing',
 'unknown': 'Unknown'
};

export class InheritanceTypes {
  available: Set<string>;

  @Validate(SetNotEmpty, {
    message: 'select at least one'
  })
  selected: Set<string> = new Set();

  constructor(available: Array<string>) {
    this.available = new Set(available);
  }
}
