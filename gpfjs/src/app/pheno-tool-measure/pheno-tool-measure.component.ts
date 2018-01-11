import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { Observable } from 'rxjs';
import { validationErrorsToStringArray, toValidationObservable } from '../utils/to-observable-with-validation';
import { PhenoToolMeasure }  from './pheno-tool-measure';
import { ValidationError } from 'class-validator';

@Component({
  selector: 'gpf-pheno-tool-measure',
  templateUrl: './pheno-tool-measure.component.html',
  styleUrls: ['./pheno-tool-measure.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PhenoToolMeasureComponent)
  }]
})
export class PhenoToolMeasureComponent extends QueryStateWithErrorsProvider implements OnInit {
  phenoToolMeasure = new PhenoToolMeasure();

  constructor() {
    super();
  }

  ngOnInit() {
  }

  getState() {
    return this.validateAndGetState(this.phenoToolMeasure)
      .map(state => ({
        measureId: state.measure.name,
        normalizeBy: state.normalizeBy
      }));
  }

  onNormalizeByChange(value: any, event): void {
    if (event.target.checked) {
      if (this.phenoToolMeasure.normalizeBy.indexOf(value) === -1) {
        this.phenoToolMeasure.normalizeBy.push(value);
      }
    } else {
      if (this.phenoToolMeasure.normalizeBy.indexOf(value) !== -1) {
        this.phenoToolMeasure.normalizeBy =
          this.phenoToolMeasure.normalizeBy.filter(v => v !== value);
      }
    }
  }

}
