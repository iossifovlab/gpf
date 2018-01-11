import {
    ValidatorConstraint, ValidatorConstraintInterface, ValidationArguments
} from 'class-validator';

@ValidatorConstraint({
    name: 'customText',
    async: false
})
export class SetNotEmpty implements ValidatorConstraintInterface {

    validate<T>(s: Set<T>, args: ValidationArguments) {
        return s.size !== 0;
    }

    defaultMessage(args: ValidationArguments) {
        return 'Set is empty!';
    }

}
