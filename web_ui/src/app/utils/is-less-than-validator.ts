import { registerDecorator, ValidationOptions, ValidationArguments } from 'class-validator';

export function IsLessThanOrEqual(
  property: string,
  validationOptions?: ValidationOptions,
): (object: object, propertyName: string) => void {
  return function(object: object, propertyName: string): void {
    registerDecorator({
      name: 'isLessThanOrEqual',
      target: object.constructor,
      propertyName: propertyName,
      options: validationOptions,
      constraints: [property],
      validator: {
        validate: function(value: unknown, args: ValidationArguments): boolean {
          const [relatedPropertyName] = args.constraints as [string];
          try {
            const relatedValue = relatedPropertyName
              .split('.')
              .reduce<unknown>(
                (a, b) => (a as Record<string, unknown>)[b],
                args.object,
              );
            if (relatedValue === null) {
              return true;
            }
            return typeof value === 'number' &&
               typeof relatedValue === 'number' &&
               value <= relatedValue;
          } catch (_exception) {
            return false;
          }
        },
        defaultMessage: function(args: ValidationArguments): string {
          const [relatedPropertyName] = args.constraints as [string];
          return `${propertyName} should be less than or equal to ${relatedPropertyName}`;
        }
      }
    });
  };
}
