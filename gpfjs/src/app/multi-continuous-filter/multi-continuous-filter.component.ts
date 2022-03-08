import { Component, OnInit, Input, EventEmitter, Output, ViewChild } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { ContinuousFilterState } from '../person-filters/person-filters';
import { PersonFilter } from '../datasets/datasets';
import { Store } from '@ngxs/store';
import { StatefulComponent } from 'app/common/stateful-component';
import { PersonFiltersState } from 'app/person-filters/person-filters.state';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';

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

  @ViewChild(PhenoMeasureSelectorComponent) private measureSelectorComponent: PhenoMeasureSelectorComponent;
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

  public async restoreContinuousFilter(state) {
    if (!state['personFiltersState']) {
      return;
    }
    const filters = state['personFiltersState'][this.isFamilyFilter ? 'familyFilters' : 'personFilters'];
    filters.forEach(async (filter) => {
      let selection = {
        name: filter.source,
        min: filter['selection']['min'],
        max: filter['selection']['max']
      };
      this.selectedMeasure = selection;
      await this.waitForSelectorComponent();
      this.measureSelectorComponent.selectMeasure(this.selectedMeasure);
    });
  }

  private async waitForSelectorComponent() {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.measureSelectorComponent !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  set selectedMeasure(measure) {
    this.internalSelectedMeasure = measure;
    if (measure)  {
      this.continuousFilterState.source = measure.name;
      this.continuousFilterState.selection['min'] = measure.min;
      this.continuousFilterState.selection['max'] = measure.max;
    } else {
      this.continuousFilterState.source = null;
    }
    this.updateFilterEvent.emit();
  }

  get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }
}
