import { Input, Directive } from '@angular/core';
import { NG_VALIDATORS, Validator, AbstractControl } from '@angular/forms';

@Directive({
    selector: '[min][formControlName],[min][formControl],[min][ngModel]',
    providers: [{ provide: NG_VALIDATORS, useExisting: MinValidatorDirective, multi: true }],
    host: { '[attr.min]': 'min ? min : null' },
    standalone: false
})
export class MinValidatorDirective implements Validator {
  @Input() public min: number;

  public validate(control: AbstractControl): {[key: string]: any} {
    return Number(control.value) >= Number(this.min) ? null : {'min': true};
  }
}

@Directive({
    selector: '[max][formControlName],[max][formControl],[max][ngModel]',
    providers: [{ provide: NG_VALIDATORS, useExisting: MaxValidatorDirective, multi: true }],
    host: { '[attr.max]': 'max ? max : null' },
    standalone: false
})
export class MaxValidatorDirective implements Validator {
  @Input() public max: number;

  public validate(control: AbstractControl): {[key: string]: any} {
    return Number(control.value) <= Number(this.max) ? null : {'max': true};
  }
}
