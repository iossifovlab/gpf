import { Input, Component, OnInit, ViewChild, ViewEncapsulation, Output, EventEmitter, Directive, OnChanges, SimpleChanges, ChangeDetectorRef } from '@angular/core';
import { FormControl, NG_VALIDATORS, Validator, Validators, ValidatorFn, AbstractControl } from '@angular/forms';
import { GeneWeights, Partitions } from './gene-weights';
import { GeneWeightsService } from './gene-weights.service';
import { Subject }           from 'rxjs/Subject';
import { Observable }        from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';
import 'rxjs/add/operator/switchMap';
import 'rxjs/add/observable/of';

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
  private rangeChanges = new Subject<Array<number >>();
  private partitions: Observable<Partitions>;

  private internalSelectedGeneWeights: GeneWeights;

  geneWeightsArray: GeneWeights[];
  private internalRangeStart: number;
  private internalRangeEnd: number;

  private rangesCounts: Array<number>;

  constructor(private geneWeightsService: GeneWeightsService, private changeDetectorRef: ChangeDetectorRef) {

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


    this.partitions = this.rangeChanges
      .debounceTime(300)
      .distinctUntilChanged()
      .switchMap(term => {
        return this.geneWeightsService.getPartitions(this.selectedGeneWeights.desc, this.internalRangeStart, this.internalRangeEnd);
      })
      .catch(error => {
        console.log(error);
        return null;
      });

    this.partitions.subscribe(
      (partitions) => {
        this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
  }


  set rangeStart(range: number) {
    this.internalRangeStart = range;
    this.rangeChanges.next([this.internalRangeStart, this.internalRangeEnd]);
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  set rangeEnd(range: number) {
    this.internalRangeEnd = range;
    this.rangeChanges.next([this.internalRangeStart, this.internalRangeEnd]);
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }
}
