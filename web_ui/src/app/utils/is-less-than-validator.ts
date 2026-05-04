import { registerDecorator, ValidationOptions, ValidationArguments } from 'class-validator';

export function IsLessThanOrEqual(property: string, validationOptions?: ValidationOptions) {
  return function(object: Object, propertyName: string) {
    registerDecorator({
      name: 'isLessThanOrEqual',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      constraints: [property],
      validator: {
        validate: function(value: any, args: ValidationArguments): boolean {
          const [relatedPropertyName] = args.constraints;
          try {
            const relatedValue = relatedPropertyName.split('.').reduce((a, b) => a[b], args.object as any);
            if (relatedValue === null) {
              return true;
            }
            return typeof value === 'number' &&
               typeof relatedValue === 'number' &&
               value <= relatedValue;
          } catch (exception) {
            return false;
          }
        },
        defaultMessage: function(args: ValidationArguments): string {
          const [relatedPropertyName] = args.constraints;
          return `${propertyName} should be less than or equal to ${relatedPropertyName}`;
        }
      }
    });
  };
}
