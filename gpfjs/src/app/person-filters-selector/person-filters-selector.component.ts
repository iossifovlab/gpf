import { Component, Input, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store } from '@ngrx/store';
import { cloneDeep } from 'lodash';
import { take } from 'rxjs';
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
import { resetErrors } from 'app/common/errors.state';

@Component({
  selector: 'gpf-person-filters-selector',
  templateUrl: './person-filters-selector.component.html',
  styleUrls: ['./person-filters-selector.component.css'],
})
export class PersonFiltersSelectorComponent implements OnInit {
  @Input() public dataset: Dataset;
  public selectedMeasureHistograms: {measureHistogram: MeasureHistogram, state: MeasureHistogramState}[] = [];
  @Input() public isFamilyFilters: boolean;

  public selectedDatasetId: string;

  // @Equals(true, {message: 'Select at least one continuous filter.'})
  public areFiltersSelected = false;

  public constructor(protected store: Store, private measuresService: MeasuresService) {}

  public ngOnInit(): void {
    this.selectedDatasetId = this.dataset.id;
    if (this.isFamilyFilters) {
      this.store.select(selectFamilyMeasureHistograms).subscribe((state: MeasureHistogramState[]) => {
        this.areFiltersSelected = Boolean(state?.length);
      });

      this.store.select(selectFamilyMeasureHistograms).pipe(take(1)).subscribe((state: MeasureHistogramState[]) => {
        if (state) {
          const clonedState = cloneDeep(state);
          this.loadState(clonedState);
        }
      });
    } else {
      this.store.select(selectPersonMeasureHistograms).subscribe((state: MeasureHistogramState[]) => {
        this.areFiltersSelected = Boolean(state?.length);
      });

      this.store.select(selectPersonMeasureHistograms).pipe(take(1)).subscribe((state: MeasureHistogramState[]) => {
        if (state) {
          const clonedState = cloneDeep(state);
          this.loadState(clonedState);
        }
      });
    }
  }

  public addMeasure(measure: Measure): void {
    if (measure) {
      this.measuresService.getMeasureHistogramBeta(this.dataset.id, measure.id)
        .subscribe(histogramData => {
          const defaultState = this.createMeasureDefaultState(histogramData);
          this.selectedMeasureHistograms.push({
            measureHistogram: histogramData,
            state: defaultState
          });

          if (defaultState.histogramType === 'continuous') {
            const continuousHistogram = {
              measure: defaultState.measure,
              rangeStart: defaultState.rangeStart,
              rangeEnd: defaultState.rangeEnd
            };
            this.dispatchContinuousHistogram(continuousHistogram);
          } else {
            const categoricalHistogram = {
              measure: defaultState.measure,
              values: defaultState.values,
              categoricalView: defaultState.categoricalView
            };
            this.dispatchCategoricalHistogram(categoricalHistogram);
          }
        });
    }
  }

  private dispatchContinuousHistogram(histogram: { measure: string; rangeStart: number; rangeEnd: number; }): void {
    if (this.isFamilyFilters) {
      this.store.dispatch(setFamilyMeasureHistogramsContinuous(histogram));
    } else {
      this.store.dispatch(setPersonMeasureHistogramsContinuous(histogram));
    }
  }

  private dispatchCategoricalHistogram(
    histogram: { measure: string; values: string[]; categoricalView: CategoricalHistogramView }
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
    };
    state.measure = measureHistogram.measure;
    if (measureHistogram.histogram instanceof CategoricalHistogram) {
      state.histogramType = 'categorical';
      state.rangeStart = null;
      state.rangeEnd = null;
      state.values = measureHistogram.histogram.values.map(value => value.name);
      state.categoricalView = 'range selector';
    } else {
      state.histogramType = 'continuous';
      state.rangeStart = measureHistogram.histogram.rangeMin;
      state.rangeEnd = measureHistogram.histogram.rangeMax;
      state.values = null;
      state.categoricalView = null;
    }
    return state;
  }

  private loadState(states: MeasureHistogramState[]): void {
    states.forEach(state => {
      this.measuresService.getMeasureHistogramBeta(this.dataset.id, state.measure)
        .subscribe(histogramData => {
          this.selectedMeasureHistograms.push({
            measureHistogram: histogramData,
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
  }

  private saveFamilyFilterToState(state: MeasureHistogramState): void {
    if (state.histogramType === 'continuous') {
      this.store.dispatch(setFamilyMeasureHistogramsContinuous({
        measure: state.measure,
        rangeStart: state.rangeStart,
        rangeEnd: state.rangeEnd,
      }));
    } else if (state.histogramType === 'categorical') {
      this.store.dispatch(setFamilyMeasureHistogramsCategorical({
        measure: state.measure,
        values: state.values,
        categoricalView: state.categoricalView,
      }));
    }
  }

  private savePersonFilterToState(state: MeasureHistogramState): void {
    if (state.histogramType === 'continuous') {
      this.store.dispatch(setPersonMeasureHistogramsContinuous({
        measure: state.measure,
        rangeStart: state.rangeStart,
        rangeEnd: state.rangeEnd,
      }));
    } else if (state.histogramType === 'categorical') {
      this.store.dispatch(setPersonMeasureHistogramsCategorical({
        measure: state.measure,
        values: state.values,
        categoricalView: state.categoricalView,
      }));
    }
  }

  public removeFromState(measure: string): void {
    const index = this.selectedMeasureHistograms.findIndex(hist => hist.state.measure === measure);
    this.selectedMeasureHistograms.splice(index, 1);

    if (this.isFamilyFilters) {
      this.store.dispatch(removeFamilyMeasureHistogram({familyMeasureHistogramName: measure}));
      this.store.dispatch(resetErrors({componentId: `familyFilters: ${measure}`}));
    } else {
      this.store.dispatch(removePersonMeasureHistogram({personMeasureHistogramName: measure}));
      this.store.dispatch(resetErrors({componentId: `personFilters: ${measure}`}));
    }
  }
}

