import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { Observable, ReplaySubject } from 'rxjs';
import { validationErrorsToStringArray, toValidationObservable } from '../utils/to-observable-with-validation';
import { PhenoToolMeasure }  from './pheno-tool-measure';
import { ValidationError } from 'class-validator';
import { StateRestoreService } from '../store/state-restore.service';
import { ContinuousMeasure } from '../measures/measures';

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

  measuresLoaded$ = new ReplaySubject<Array<ContinuousMeasure>>()

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    Observable.combineLatest(
      this.stateRestoreService.getState(this.constructor.name),
      this.measuresLoaded$)
      .take(1)
      .subscribe(([state, measures]) => {
        if (state['measureId'] && state['normalizeBy']) {
          this.phenoToolMeasure.measure = 
            measures.find(m => m.name === state['measureId']);

          this.phenoToolMeasure.normalizeBy = state['normalizeBy'];
        }
      });
  }

  getState() {
    return this.validateAndGetState(this.phenoToolMeasure)
      .map(state => ({
        measureId: state.measure.name,
        normalizeBy: state.normalizeBy
      }));
  }

  measuresUpdate(measures: Array<ContinuousMeasure>) {
    this.measuresLoaded$.next(measures);
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
