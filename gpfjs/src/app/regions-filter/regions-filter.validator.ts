import { Input, Directive } from '@angular/core';
import { ValidatorConstraint, ValidatorConstraintInterface, ValidationArguments } from "class-validator";

@ValidatorConstraint({ name: "customText", async: false })
export class RegionsFilterValidator implements ValidatorConstraintInterface {
    validate(text: string, args: ValidationArguments) {
      if (!text) {
        return null;
      }

      let valid = true;
      for (var line of text.split(/[/,\s]+/)) {
        var match = line.match(/^(?:chr)?(?:[0-9xX]|[0-1][0-9]|2[0-2]):([0-9,]+)(?:\-([0-9,]+))?$/i)
        if (match === null) {
          valid = false;
        }

        else if (match.length >= 3 && match[1] && match[2]
                 && +match[1].replace(",", "") > +match[2].replace(",", "")) {
          valid = false;
        }
       }
      return valid;
    }

    defaultMessage(args: ValidationArguments) { // here you can provide default error message if validation failed
        return "Invalid region!";
    }

}
