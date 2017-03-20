import {registerDecorator, ValidationOptions, ValidationArguments} from "class-validator";

export function IsLessThanOrEqual(property: string, validationOptions?: ValidationOptions) {
   return function (object: Object, propertyName: string) {
        registerDecorator({
            name: "isLessThanOrEqual",
            target: object.constructor,
            propertyName: propertyName,
            options: validationOptions,
            constraints: [property],
            validator: {
                validate(value: any, args: ValidationArguments) {
                    const [relatedPropertyName] = args.constraints;
                    const relatedValue = (args.object as any)[relatedPropertyName];
                    return  typeof value === "number" &&
                           typeof relatedValue === "number" &&
                           value <= relatedValue;
                },
                defaultMessage(args: ValidationArguments) {
                  const [relatedPropertyName] = args.constraints;

                  return `${propertyName} should be less than or equal to ${relatedPropertyName}`;
                }
            }
        });
   };
}
