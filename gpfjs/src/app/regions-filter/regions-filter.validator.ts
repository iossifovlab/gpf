import { Input, Directive } from '@angular/core';
import { NG_VALIDATORS, Validator, Validators, AbstractControl } from '@angular/forms';


@Directive({
  selector: '[regionsFilter][formControlName],[regionsFilter][formControl],[regionsFilter][ngModel]',
  providers: [{provide: NG_VALIDATORS, useExisting: RegionsFilterValidatorDirective, multi: true}],
})
export class RegionsFilterValidatorDirective implements Validator {
  validate(control: AbstractControl): {[key: string]: any} {
    return /^(chr)?([0-9xX]|[0-1][0-9]|2[0-2]):[0-9]+(\-[0-9]+)?$/ig.test(control.value) ? null : {'regionsFilter': true};
  }
}
