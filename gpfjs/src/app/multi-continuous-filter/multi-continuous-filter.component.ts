import { Component, OnInit, Input, forwardRef, ViewChild } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { QueryStateCollector } from '../query/query-state-provider';
import { ContinuousFilterState } from '../pheno-filters/pheno-filters';
import { PhenoFilter } from '../datasets/datasets';
import { Observable } from 'rxjs/Observable';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: forwardRef(() => MultiContinuousFilterComponent)
  }]
})
export class MultiContinuousFilterComponent extends QueryStateCollector implements OnInit {
  @Input() datasetId: string;
  @Input() continuousFilter: PhenoFilter;
  @Input() continuousFilterState: ContinuousFilterState;

  measures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
  }

  restoreContinuousFilter(state) {
    let filter = state.find(f => f.id === this.continuousFilterState.id);
    if (filter) {
      this.continuousFilterState.measure = filter.measure;
      this.continuousFilterState.domainMin = filter.domainMin;
      this.continuousFilterState.domainMax = filter.domainMax;
      this.continuousFilterState.mmax = filter.mmax;
      this.continuousFilterState.mmin = filter.mmin;
      if (this.measures) {
        let measure = this.measures.find(m => m.name === filter.measure);
        if (measure) {
          this.internalSelectedMeasure = measure;
        }
      }
    }
  }

  set selectedMeasure(measure) {
    this.continuousFilterState.measure = measure ? measure.name : null;
    this.continuousFilterState.domainMin = measure ? measure.min : 0;
    this.continuousFilterState.domainMax = measure ? measure.max : 0;
    this.internalSelectedMeasure = measure;
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }

  updateMeasures(measures) {
    this.measures = measures;

    this.stateRestoreService
      .getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['phenoFilters']) {
          this.restoreContinuousFilter(state['phenoFilters']);
        }
      });
  }

}
