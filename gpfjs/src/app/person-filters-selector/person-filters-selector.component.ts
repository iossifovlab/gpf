import { Component, Input, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store } from '@ngrx/store';
import { Equals } from 'class-validator';
import { ComponentValidator } from 'app/common/component-validator';
import { cloneDeep } from 'lodash';
import { take } from 'rxjs';
import { MeasuresService } from 'app/measures/measures.service';
import { ContinuousMeasure, MeasureHistogram } from 'app/measures/measures';

@Component({
  selector: 'gpf-person-filters-selector',
  templateUrl: './person-filters-selector.component.html',
  styleUrls: ['./person-filters-selector.component.css'],
})
export class PersonFiltersSelectorComponent implements OnInit {
  @Input() public dataset: Dataset;
  public measureHistograms: MeasureHistogram[] = [];
  @Input() public isFamilyFilters: boolean;

  public selectedDatasetId: string;
  // public categoricalFilters: PersonFilterState[] = [];
  // public continuousFilters: PersonFilterState[] = [];

  // @Equals(true, {message: 'Select at least one continuous filter.'})
  public areFiltersSelected = false;

  public constructor(protected store: Store, private measuresService: MeasuresService) {}

  public ngOnInit(): void {
    this.selectedDatasetId = this.dataset.id;
    // this.store.select(selectPersonFilters).subscribe((state: PersonAndFamilyFilters) => {
    //   if (this.isFamilyFilters) {
    //     this.areFiltersSelected = Boolean(state.familyFilters?.filter(f => f.sourceType === 'continuous').length);
    //   } else {
    //     this.areFiltersSelected = Boolean(state.personFilters?.filter(f => f.sourceType === 'continuous').length);
    //   }
    // });

    // this.store.select(selectPersonFilters).pipe(take(1)).subscribe((state: PersonAndFamilyFilters) => {
    //   const clonedState = cloneDeep(state);
    //   this.setDefaultFilters();
    //   this.setFiltersFromState(clonedState);
    // });

    // super.ngOnInit();
  }

  public addMeasure(measure: ContinuousMeasure): void {
    // this.internalSelectedMeasure = measure;
    if (measure) {
      this.measuresService.getMeasureHistogramBeta(this.dataset.id, measure.name)
        .subscribe(histogramData => {
          this.measureHistograms.push(histogramData);
          // const selection = this.continuousFilterState.selection as ContinuousSelection;
          // this.histogramData = histogramData;
          // if (!selection.min) {
          //   selection.min = histogramData.min;
          // }
          // if (!selection.max) {
          //   selection.max = histogramData.max;
          // }
        });
      //   this.continuousFilterState.source = measure.name;
      //   this.continuousFilterState.selection['min'] = measure.min;
      //   this.continuousFilterState.selection['max'] = measure.max;

    //   if (this.isFamilyFilters) {
    //     this.store.dispatch(updateFamilyFilter({familyFilter: cloneDeep(this.continuousFilterState)}));
    //   } else {
    //     this.store.dispatch(updatePersonFilter({personFilter: cloneDeep(this.continuousFilterState)}));
    //   }
    // } else if (this.isFamilyFilters) {
    //   this.store.dispatch(removeFamilyFilter({familyFilter: cloneDeep(this.continuousFilterState)}));
    // } else {
    //   this.store.dispatch(removePersonFilter({personFilter: cloneDeep(this.continuousFilterState)}));
    }
  }

  private setDefaultFilters(): void {
    // const defaultFilters = this.isFamilyFilters ?
    //   this.dataset.genotypeBrowserConfig.familyFilters : this.dataset.genotypeBrowserConfig.personFilters;

    // for (const defaultFilter of defaultFilters) {
      // if (defaultFilter.sourceType === 'continuous') {
      //   this.continuousFilters.push(
      //     new ContinuousFilterState(
      //       defaultFilter.name,
      //       defaultFilter.sourceType,
      //       defaultFilter.role,
      //       defaultFilter.source,
      //       defaultFilter.from,
      //     )
      //   );
      // } else if (defaultFilter.sourceType === 'categorical') {
      //   this.categoricalFilters.push(
      //     new CategoricalFilterState(
      //       defaultFilter.name,
      //       defaultFilter.sourceType,
      //       defaultFilter.role,
      //       defaultFilter.source,
      //       defaultFilter.from,
      //     )
      //   );
      // } else {
      //   console.error(`Unexpected filter type:${defaultFilter.sourceType} in ${defaultFilter.name}`);
      // }
    // }
  }

  // private setFiltersFromState(state: PersonAndFamilyFilters): void {
    // const filters: PersonFilterState[] = this.isFamilyFilters ? state.familyFilters : state.personFilters;
    // if (!filters) {
    //   return;
    // }
    // for (const filter of filters) {
      // if (filter.sourceType === 'continuous') {
      //   const existingIndex = this.continuousFilters.findIndex(f => f.id ===filter.id);
      //   if (existingIndex !== -1) {
      //     this.continuousFilters[existingIndex] = filter;
      //   } else {
      //     this.continuousFilters.push(filter);
      //   }
      // } else if (filter.sourceType === 'categorical') {
      //   const existingIndex = this.categoricalFilters.findIndex(f => f.id ===filter.id);
      //   if (existingIndex !== -1) {
      //     this.categoricalFilters[existingIndex] = filter;
      //   } else {
      //     this.categoricalFilters.push(filter);
      //   }
      // } else {
      //   console.error(`Unexpected filter type:${filter.sourceType} in ${filter.id}`);
      // }
    // }
  // }
}
