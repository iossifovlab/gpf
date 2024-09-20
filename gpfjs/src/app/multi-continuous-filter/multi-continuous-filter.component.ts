import { Component, OnInit, Input, ViewChild } from '@angular/core';
import { ContinuousMeasure } from '../measures/measures';
import { ContinuousFilterState, ContinuousSelection} from '../person-filters/person-filters';
import { Store } from '@ngrx/store';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import {
  removeFamilyFilter,
  removePersonFilter,
  selectPersonFilters,
  updateFamilyFilter,
  updatePersonFilter
} from 'app/person-filters/person-filters.state';
import { ComponentValidator } from 'app/common/component-validator';
import { take } from 'rxjs';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-multi-continuous-filter',
  templateUrl: './multi-continuous-filter.component.html',
  styleUrls: ['./multi-continuous-filter.component.css'],
})
export class MultiContinuousFilterComponent extends ComponentValidator implements OnInit {
  @Input() public datasetId: string;
  @Input() public continuousFilter: ContinuousFilterState;
  @Input() public isFamilyFilters: boolean;
  public continuousFilterState: ContinuousFilterState;


  @ViewChild(PhenoMeasureSelectorComponent) private measureSelectorComponent: PhenoMeasureSelectorComponent;
  public measures: Array<ContinuousMeasure>;
  public internalSelectedMeasure: ContinuousMeasure;

  public constructor(protected store: Store) {
    super(store, 'personFilters', selectPersonFilters);
  }

  public ngOnInit(): void {
    this.store.select(selectPersonFilters).pipe(take(1)).subscribe((state) => {
      let stateFilter: ContinuousFilterState;

      if (this.isFamilyFilters) {
        stateFilter = state.familyFilters?.find(filter => filter.id === this.continuousFilter.id);
      } else {
        stateFilter = state.personFilters?.find(filter => filter.id === this.continuousFilter.id);
      }

      if (stateFilter) {
        this.continuousFilterState = cloneDeep(stateFilter);

        this.loadMeasureFromState(stateFilter);
      } else {
        this.continuousFilterState = cloneDeep(this.continuousFilter);
      }
    });
  }

  private async loadMeasureFromState(stateFilter: ContinuousFilterState): Promise<void> {
    await this.waitForSelectorComponent();
    this.measureSelectorComponent.selectMeasure(
      new ContinuousMeasure(
        stateFilter.source,
        (stateFilter.selection as ContinuousSelection).min,
        (stateFilter.selection as ContinuousSelection).max
      ));
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

      if (this.isFamilyFilters) {
        this.store.dispatch(updateFamilyFilter({familyFilter: cloneDeep(this.continuousFilterState)}));
      } else {
        this.store.dispatch(updatePersonFilter({personFilter: cloneDeep(this.continuousFilterState)}));
      }
    } else if (this.isFamilyFilters) {
      this.store.dispatch(removeFamilyFilter({familyFilter: cloneDeep(this.continuousFilterState)}));
    } else {
      this.store.dispatch(removePersonFilter({personFilter: cloneDeep(this.continuousFilterState)}));
    }
  }

  public get selectedMeasure(): ContinuousMeasure {
    return this.internalSelectedMeasure;
  }
}
