import { Input, Directive } from '@angular/core';
import {
  ValidatorConstraint, ValidatorConstraintInterface, ValidationArguments
} from 'class-validator';

@ValidatorConstraint({ name: 'customText', async: false })
export class RegionsFilterValidator implements ValidatorConstraintInterface {

  private static LINE_REGEX = new RegExp(
    "^(?:chr)?(?:[0-9xX]|[0-1][0-9]|2[0-2]):([0-9,]+)(?:\-([0-9,]+))?$", "i");

  validate(text: string, args: ValidationArguments) {
    if (!text) {
      return null;
    }

    let valid = true;
    let lines = text.split('\n')
      .map(t => t.trim())
      .filter(t => !!t);
    
    if(lines.length === 0) {
      valid = false;
    }

    for (let line of lines) {
      valid = valid && this.isValid(line);  
    }

    return valid;
  }

  private isValid(line: string) {
    let match = line.match(RegionsFilterValidator.LINE_REGEX);
    if (match === null) {
      return false;
    }

    if (match.length >= 3 && match[1] && match[2]
        && +match[1].replace(',', '') > +match[2].replace(',', '')) {
      return false;
    }

    return true;
  }

  defaultMessage(args: ValidationArguments) {
      return 'Invalid region!';
  }

}
