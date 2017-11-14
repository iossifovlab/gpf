import { PedigreeSelector } from '../datasets/datasets';
import { ArrayNotEmpty } from 'class-validator';

export class PedigreeSelectorState {
  pedigree: PedigreeSelector = null;

  @ArrayNotEmpty({
    message: 'select at least one'
  })
  checkedValues = new Set();
};

