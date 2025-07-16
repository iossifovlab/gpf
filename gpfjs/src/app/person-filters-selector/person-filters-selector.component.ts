import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { Observable, Subscription, take, zip } from 'rxjs';
import { MeasuresService } from 'app/measures/measures.service';
import { Measure, MeasureHistogram } from 'app/measures/measures';
import {
  MeasureHistogramState,
  removeFamilyMeasureHistogram,
  removePersonMeasureHistogram,
  selectFamilyMeasureHistograms,
  selectPersonMeasureHistograms,
  setFamilyMeasureHistogramsCategorical,
  setFamilyMeasureHistogramsContinuous,
  setPersonMeasureHistogramsCategorical,
  setPersonMeasureHistogramsContinuous
} from './measure-histogram.state';
import { CategoricalHistogram, CategoricalHistogramView } from 'app/utils/histogram-types';
import { resetErrors, setErrors } from 'app/common/errors.state';

@Component({
    selector: 'gpf-person-filters-selector',
    templateUrl: './person-filters-selector.component.html',
    styleUrls: ['./person-filters-selector.component.css'],
    standalone: false
})
export class PersonFiltersSelectorComponent implements OnInit, OnDestroy {
  @Input() public dataset: Dataset;
  public selectedMeasureHistograms: {measureHistogram: MeasureHistogram, state: MeasureHistogramState}[] = [];
  @Input() public isFamilyFilters: boolean;

  public selectedDatasetId: string;

  public errors: string[] = [];
  public areFiltersSelected = false;

  public selectMeasureHistogramsSubscription = new Subscription();

  public constructor(protected store: Store, private measuresService: MeasuresService) { }

  public ngOnInit(): void {
    this.selectedDatasetId = this.dataset.id;
    if (this.isFamilyFilters) {
      this.selectMeasureHistogramsSubscription = this.store.select(selectFamilyMeasureHistograms)
        .subscribe((state: MeasureHistogramState[]) => {
          this.areFiltersSelected = Boolean(state?.length);
          this.validateState();
        });

      this.store.select(selectFamilyMeasureHistograms).pipe(take(1)).subscribe((state: MeasureHistogramState[]) => {
        if (state) {
          const clonedState = cloneDeep(state);
          this.loadState(clonedState);
        }
      });
    } else {
      this.selectMeasureHistogramsSubscription = this.store.select(selectPersonMeasureHistograms)
        .subscribe((state: MeasureHistogramState[]) => {
          this.areFiltersSelected = Boolean(state?.length);
          this.validateState();
        });

      this.store.select(selectPersonMeasureHistograms).pipe(take(1)).subscribe((state: MeasureHistogramState[]) => {
        if (state) {
          const clonedState = cloneDeep(state);
          this.loadState(clonedState);
        }
      });
    }
  }

  public ngOnDestroy(): void {
    let componentId = 'personFilters';
    if (this.isFamilyFilters) {
      componentId = 'familyFilters';
    }
    this.store.dispatch(resetErrors({componentId: `${componentId}`}));
    this.selectMeasureHistogramsSubscription.unsubscribe();
  }

  public addMeasure(measure: Measure): void {
    if (measure) {
      this.measuresService.getMeasureHistogramBeta(this.dataset.id, measure.id)
        .subscribe(histogramData => {
          const defaultState = this.createMeasureDefaultState(histogramData);
          this.selectedMeasureHistograms.unshift({
            measureHistogram: histogramData,
            state: defaultState
          });

          if (defaultState.histogramType === 'continuous') {
            const continuousHistogram = {
              measure: defaultState.measure,
              rangeStart: defaultState.rangeStart,
              rangeEnd: defaultState.rangeEnd,
              roles: defaultState.roles
            };
            this.dispatchContinuousHistogram(continuousHistogram);
          } else {
            const categoricalHistogram = {
              measure: defaultState.measure,
              values: defaultState.values,
              categoricalView: defaultState.categoricalView,
              roles: defaultState.roles
            };
            this.dispatchCategoricalHistogram(categoricalHistogram);
          }
        });
    }
    this.validateState();
  }

  public loadHistogram(data: {measureId: string, roles: string[]}): void {
    this.measuresService.getMeasureHistogramBeta(this.dataset.id, data.measureId, data.roles)
      .subscribe(histogramData => {
        const index = this.removeFromState(data.measureId);
        const defaultState = this.createMeasureDefaultState(histogramData);
        defaultState.roles = data.roles;

        this.selectedMeasureHistograms.splice(index, 0, {
          measureHistogram: histogramData,
          state: defaultState
        });
        this.addToState(defaultState);
      });
  }

  private dispatchContinuousHistogram(
    histogram: { measure: string; rangeStart: number; rangeEnd: number; roles: string[] }
  ): void {
    if (this.isFamilyFilters) {
      this.store.dispatch(setFamilyMeasureHistogramsContinuous(histogram));
    } else {
      this.store.dispatch(setPersonMeasureHistogramsContinuous(histogram));
    }
  }

  private dispatchCategoricalHistogram(
    histogram: { measure: string; values: string[]; categoricalView: CategoricalHistogramView, roles: string[] }
  ): void {
    if (this.isFamilyFilters) {
      this.store.dispatch(setFamilyMeasureHistogramsCategorical(histogram));
    } else {
      this.store.dispatch(setPersonMeasureHistogramsCategorical(histogram));
    }
  }

  private createMeasureDefaultState(measureHistogram: MeasureHistogram): MeasureHistogramState {
    const state: MeasureHistogramState = {
      histogramType: null,
      measure: null,
      rangeStart: null,
      rangeEnd: null,
      values: null,
      categoricalView: null,
      roles: null
    };
    state.measure = measureHistogram.measure;
    if (measureHistogram.histogram instanceof CategoricalHistogram) {
      state.histogramType = 'categorical';
      state.rangeStart = null;
      state.rangeEnd = null;
      state.values = measureHistogram.histogram.values.map(value => value.name);
      state.categoricalView = 'range selector';
      state.roles = null;
    } else {
      state.histogramType = 'continuous';
      state.rangeStart = measureHistogram.histogram.rangeMin;
      state.rangeEnd = measureHistogram.histogram.rangeMax;
      state.values = null;
      state.categoricalView = null;
      state.roles = null;
    }
    return state;
  }

  private loadState(states: MeasureHistogramState[]): void {
    const observables: Observable<MeasureHistogram>[] = [];
    states.forEach(state => {
      observables.push(this.measuresService.getMeasureHistogramBeta(this.dataset.id, state.measure, state.roles));
    });

    zip(...observables).subscribe(allHistogramsData => {
      states.forEach((state, i) => {
        this.selectedMeasureHistograms.unshift({
          measureHistogram: allHistogramsData[i],
          state: state
        });
      });
    });
  }

  public addToState(state: MeasureHistogramState): void {
    state = cloneDeep(state);
    if (this.isFamilyFilters) {
      this.saveFamilyFilterToState(state);
    } else {
      this.savePersonFilterToState(state);
    }
    this.validateState();
  }

  private saveFamilyFilterToState(state: MeasureHistogramState): void {
    if (state.histogramType === 'continuous') {
      this.store.dispatch(setFamilyMeasureHistogramsContinuous({
        measure: state.measure,
        rangeStart: state.rangeStart,
        rangeEnd: state.rangeEnd,
        roles: state.roles
      }));
    } else if (state.histogramType === 'categorical') {
      this.store.dispatch(setFamilyMeasureHistogramsCategorical({
        measure: state.measure,
        values: state.values,
        categoricalView: state.categoricalView,
        roles: state.roles
      }));
    }
  }

  private savePersonFilterToState(state: MeasureHistogramState): void {
    if (state.histogramType === 'continuous') {
      this.store.dispatch(setPersonMeasureHistogramsContinuous({
        measure: state.measure,
        rangeStart: state.rangeStart,
        rangeEnd: state.rangeEnd,
        roles: state.roles
      }));
    } else if (state.histogramType === 'categorical') {
      this.store.dispatch(setPersonMeasureHistogramsCategorical({
        measure: state.measure,
        values: state.values,
        categoricalView: state.categoricalView,
        roles: state.roles
      }));
    }
  }

  public removeFromState(measure: string): number {
    const index = this.selectedMeasureHistograms.findIndex(hist => hist.state.measure === measure);
    this.selectedMeasureHistograms.splice(index, 1);

    if (this.isFamilyFilters) {
      this.store.dispatch(removeFamilyMeasureHistogram({familyMeasureHistogramName: measure}));
      this.store.dispatch(resetErrors({componentId: `familyFilters: ${measure}`}));
    } else {
      this.store.dispatch(removePersonMeasureHistogram({personMeasureHistogramName: measure}));
      this.store.dispatch(resetErrors({componentId: `personFilters: ${measure}`}));
    }
    this.validateState();
    return index;
  }

  private validateState(): void {
    this.errors = [];
    if (!this.areFiltersSelected) {
      this.errors.push('Select a measure.');
    }

    let componentId = 'personFilters';
    if (this.isFamilyFilters) {
      componentId = 'familyFilters';
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: `${componentId}`, errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: `${componentId}`}));
    }
  }
}

