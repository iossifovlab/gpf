import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { QueryStateCollector } from '../query/query-state-provider';
import { ContinuousFilterState, ContinuousSelection } from '../pheno-filters/pheno-filters';
import { PersonFilter } from '../datasets/datasets';
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
  @Input() continuousFilter: PersonFilter;
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
    const filter = state.find(f => f.id === this.continuousFilterState.id);
    if (filter) {
      const selection = this.continuousFilterState.selection as ContinuousSelection;
      this.continuousFilterState.source = filter.measure;
      selection.domainMin = filter.domainMin;
      selection.domainMax = filter.domainMax;
      selection.max = filter.mmax;
      selection.min = filter.mmin;
      if (this.measures) {
        const measure = this.measures.find(m => m.name === filter.measure);
        if (measure) {
          this.internalSelectedMeasure = measure;
        }
      }
    }
  }

  set selectedMeasure(measure) {
    const selection = this.continuousFilterState.selection as ContinuousSelection;
    this.continuousFilterState.source = measure ? measure.name : null;
    selection.domainMin = measure ? measure.min : 0;
    selection.domainMax = measure ? measure.max : 0;
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
        if (state['personFilters']) {
          this.restoreContinuousFilter(state['personFilters']);
        }
      });
  }

}
