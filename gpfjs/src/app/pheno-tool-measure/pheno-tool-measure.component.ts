import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures'
import { QueryStateProvider } from '../query/query-state-provider'
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { PhenoToolMeasureState, PHENO_TOOL_MEASURE_CHANGE,
  PHENO_TOOL_MEASURE_INIT, PHENO_TOOL_NORMALIZE_BY_CHECK,
  PHENO_TOOL_NORMALIZE_BY_UNCHECK }  from './pheno-tool-measure';
import { ValidationError } from "class-validator";

@Component({
  selector: 'gpf-pheno-tool-measure',
  templateUrl: './pheno-tool-measure.component.html',
  styleUrls: ['./pheno-tool-measure.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => PhenoToolMeasureComponent) }]
})
export class PhenoToolMeasureComponent extends QueryStateProvider implements OnInit {
  @Input() datasetId: string;

  private phenoToolMeasureState: Observable<[PhenoToolMeasureState, boolean, ValidationError[]]>;
  internalSelectedMeasure: ContinuousMeasure;

  errors: string[];
  flashingAlert = false;

  constructor(
    private store: Store<any>
  ) {
    super();
    this.phenoToolMeasureState = toObservableWithValidation(PhenoToolMeasureState, this.store.select('phenoToolMeasure'));
  }

  ngOnInit() {
    this.store.dispatch({
      'type': PHENO_TOOL_MEASURE_INIT,
    });

    this.phenoToolMeasureState.subscribe(
      ([state, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

        this.internalSelectedMeasure = state.measure;
      }
    );
  }

  set selectedMeasure(measure) {
    this.store.dispatch({
      'type': PHENO_TOOL_MEASURE_CHANGE,
      'payload': measure
    });
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  getState() {
    return this.phenoToolMeasureState.take(1).map(
      ([state, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

          throw "invalid measure state"
        }

        return {
          measureId: state.measure.name,
          normalizeBy: state.normalizeBy
        }
      }
    );
  }

  onNormalizeByChange(value: any, event): void {
    if (event.target.checked) {
      this.store.dispatch({
        'type': PHENO_TOOL_NORMALIZE_BY_CHECK,
        'payload': value
      });
    } else {
      this.store.dispatch({
        'type': PHENO_TOOL_NORMALIZE_BY_UNCHECK,
        'payload': value
      });

    }
  }

}
