import { ValidatorConstraint, ValidatorConstraintInterface, ValidationArguments } from 'class-validator';

@ValidatorConstraint({
  name: 'customText',
  async: false
})
export class SetNotEmpty implements ValidatorConstraintInterface {
  public validate<T>(s: Set<T>, args: ValidationArguments): boolean {
    return s.size !== 0;
  }

  public defaultMessage(args: ValidationArguments): string {
    return 'Set is empty!';
  }
}
