import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection } from '../person-filters/person-filters';
import { PersonFilter } from '../datasets/datasets';

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
})
export class MultiContinuousFilterComponent implements OnInit {
  @Input() datasetId: string;
  @Input() continuousFilter: PersonFilter;
  @Input() continuousFilterState: ContinuousFilterState;
  @Output() updateFilterEvent = new EventEmitter();

  measures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;

  constructor() { }

  public ngOnInit() {

  }

  public restoreContinuousFilter(state) {
    const filter = state.find(f => f.id === this.continuousFilterState.id);
    if (filter) {
      const selection = this.continuousFilterState.selection as ContinuousSelection;
      this.continuousFilterState.source = filter.source;
      selection.domainMin = filter.domainMin;
      selection.domainMax = filter.domainMax;
      selection.max = filter.mmax;
      selection.min = filter.mmin;
      if (this.measures) {
        const measure = this.measures.find(m => m.name === filter.source);
        if (measure) {
          this.internalSelectedMeasure = measure;
        }
      }
    }
  }

  set selectedMeasure(measure) {
    if (measure)  {
      const selection = this.continuousFilterState.selection as ContinuousSelection;
      this.continuousFilterState.source = measure.name;
      selection.domainMin = measure.min;
      selection.domainMax = measure.max;
      this.internalSelectedMeasure = measure;
      this.updateFilterEvent.emit();
    } else {
      const selection = new ContinuousSelection(0, 0, 0, 0);
      this.continuousFilterState.source = null;
      this.internalSelectedMeasure = null;
      this.updateFilterEvent.emit();
    }
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }
}
