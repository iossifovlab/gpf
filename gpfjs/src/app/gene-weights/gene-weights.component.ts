import { Input, Component, OnInit, ViewChild, ViewEncapsulation, Output, EventEmitter, Directive, OnChanges, SimpleChanges } from '@angular/core';
import { FormControl, NG_VALIDATORS, Validator, Validators, ValidatorFn, AbstractControl } from '@angular/forms';
import { GeneWeights } from './gene-weights';
import { GeneWeightsService } from './gene-weights.service';


@Directive({
  selector: '[min][formControlName],[min][formControl],[min][ngModel]',
  providers: [{provide: NG_VALIDATORS, useExisting: MinValidatorDirective, multi: true}],
  host: {'[attr.min]': 'min ? min : null'}
})
export class MinValidatorDirective implements Validator {
  @Input() min: number;

  validate(control: AbstractControl): {[key: string]: any} {
    return control.value >= this.min ? null : {'min': true};
  }
}

@Directive({
  selector: '[max][formControlName],[max][formControl],[max][ngModel]',
  providers: [{provide: NG_VALIDATORS, useExisting: MaxValidatorDirective, multi: true}],
  host: {'[attr.max]': 'max ? max : null'}
})
export class MaxValidatorDirective implements Validator {
  @Input() max: number;

  validate(control: AbstractControl): {[key: string]: any} {
    return control.value <= this.max ? null : {'max': true};
  }
}


@Component({
  encapsulation: ViewEncapsulation.None,
  selector: 'gpf-gene-weights',
  templateUrl: './gene-weights.component.html'
})
export class GeneWeightsComponent {
  geneWeights: GeneWeights[];
  rangeStart: number;
  rangeEnd: number;
  initialRangeStart: number;
  initialRangeEnd: number;

  constructor(private geneWeightsService: GeneWeightsService) {

  }
  ngOnInit() {
    this.geneWeightsService.getGeneWeights().subscribe(
      (geneWeights) => {
        this.initialRangeStart = geneWeights[0].min;
        this.initialRangeEnd = geneWeights[0].max;
        this.rangeStart = geneWeights[0].min;
        this.rangeEnd = geneWeights[0].max;
        this.geneWeights = geneWeights;
      });
  }
}
