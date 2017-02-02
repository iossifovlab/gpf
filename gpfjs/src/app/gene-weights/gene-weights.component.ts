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
  private internalSelectedGeneWeights: GeneWeights;

  geneWeightsArray: GeneWeights[];
  rangeStart: number;
  rangeEnd: number;

  constructor(private geneWeightsService: GeneWeightsService) {

  }

  set selectedGeneWeights(selectedGeneWeights: GeneWeights) {
    this.internalSelectedGeneWeights = selectedGeneWeights;
    this.rangeStart = selectedGeneWeights.min;
    this.rangeEnd = selectedGeneWeights.max;
  }

  get selectedGeneWeights() {
    return this.internalSelectedGeneWeights;
  }

  ngOnInit() {
    this.geneWeightsService.getGeneWeights().subscribe(
      (geneWeights) => {
        this.geneWeightsArray = geneWeights;
        this.selectedGeneWeights = geneWeights[0];
      });
  }
}
