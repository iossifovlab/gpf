import { Component, OnInit, Input, EventEmitter, Output, ViewChild } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { ContinuousFilterState, PersonFilterState } from '../person-filters/person-filters';
import { PersonFilter } from '../datasets/datasets';
import { Store } from '@ngrx/store';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import { selectPersonFilters } from 'app/person-filters/person-filters.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { take } from 'rxjs';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
})
export class MultiContinuousFilterComponent extends StatefulComponent implements OnInit {
  @Input() public datasetId: string;
  @Input() public continuousFilter: PersonFilter;
  @Input() public continuousFilterState: ContinuousFilterState;
  @Input() public isFamilyFilter: boolean;
  @Output() public updateFilterEvent = new EventEmitter<ContinuousFilterState>();

  @ViewChild(PhenoMeasureSelectorComponent) private measureSelectorComponent: PhenoMeasureSelectorComponent;
  public measures: Array<ContinuousMeasure>;
  public internalSelectedMeasure: ContinuousMeasure;

  public constructor(protected store: Store) {
    super(store, 'personFilters', selectPersonFilters);
  }

  public ngOnInit(): void {
    this.store.select(selectPersonFilters).pipe(take(1)).subscribe(personFiltersState => {
      this.restoreContinuousFilter(cloneDeep(personFiltersState));
    });
  }

  public restoreContinuousFilter(
    state: {
      familyFilters: PersonFilterState[];
      personFilters: PersonFilterState[];
    }
  ): void {
    const filters = state[this.isFamilyFilter ? 'familyFilters' : 'personFilters'];
    filters.forEach(async(filter) => {
      if (filter.sourceType === 'continuous') {
        const selection = {
          name: filter.source,
          min: filter['selection']['min'],
          max: filter['selection']['max']
        };
        this.selectedMeasure = selection;
        await this.waitForSelectorComponent();
        this.measureSelectorComponent.selectMeasure(this.selectedMeasure);
      }
    });
  }

  private async waitForSelectorComponent(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.measureSelectorComponent !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  public set selectedMeasure(measure) {
    this.internalSelectedMeasure = measure;
    if (measure) {
      this.continuousFilterState.source = measure.name;
      this.continuousFilterState.selection['min'] = measure.min;
      this.continuousFilterState.selection['max'] = measure.max;
    } else {
      this.continuousFilterState.source = null;
    }
    this.continuousFilterState = cloneDeep(this.continuousFilterState);
    this.updateFilterEvent.emit();
  }

  public get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }
}
