import { Component, OnInit, Input, EventEmitter, Output } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection, PersonFilterState } from '../person-filters/person-filters';
import { PersonFilter } from '../datasets/datasets';
import { Store } from '@ngxs/store';
import { StatefulComponent } from 'app/common/stateful-component';
import { PersonFiltersState } from 'app/person-filters/person-filters.state';

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
})
export class MultiContinuousFilterComponent extends StatefulComponent implements OnInit {
  @Input() datasetId: string;
  @Input() continuousFilter: PersonFilter;
  @Input() continuousFilterState: ContinuousFilterState;
  @Input() isFamilyFilter: boolean;
  @Output() updateFilterEvent = new EventEmitter();

  measures: Array<ContinuousMeasure>;
  internalSelectedMeasure: ContinuousMeasure;

  constructor(protected store: Store) {
    super(store, PersonFiltersState, 'personFilters');
  }

  public ngOnInit() {
    this.store.selectOnce(state => state).subscribe(state => {
      this.restoreContinuousFilter(state);
    });
  }

  public restoreContinuousFilter(state) {
    if (!state['personFiltersState']) {
      return;
    }
    let filters;
    if(this.isFamilyFilter) {
      filters = state['personFiltersState']['familyFilters'];
    } else {
      filters = state['personFiltersState']['personFilters'];
    }
    filters.forEach(filter => {
      let selection = {
        name: filter.source,
        min: filter['selection'].min,
        max: filter['selection'].max
      };
      this.selectedMeasure = selection;
    });
  }

  set selectedMeasure(measure) {
    if (measure)  {
      this.continuousFilterState.source = measure.name;
      this.continuousFilterState.selection['min'] = measure.min;
      this.continuousFilterState.selection['max'] = measure.max;
      this.internalSelectedMeasure = measure;
      this.updateFilterEvent.emit();
    } else {
      this.continuousFilterState.source = null;
      this.internalSelectedMeasure = null;
      this.updateFilterEvent.emit();
    }
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }
}
