import { ArrayNotEmpty } from 'class-validator';

export class VariantTypes {
  @ArrayNotEmpty({
    message: 'select at least one'
  })
  selected: Set<string> = new Set();
}
