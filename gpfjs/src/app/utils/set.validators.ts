import { ValidatorConstraint, ValidatorConstraintInterface } from 'class-validator';

@ValidatorConstraint({
  name: 'customText',
  async: false
})
export class SetNotEmpty implements ValidatorConstraintInterface {
  public validate<T>(s: Set<T>): boolean {
    return s.size !== 0;
  }

  public defaultMessage(): string {
    return 'Set is empty!';
  }
}
