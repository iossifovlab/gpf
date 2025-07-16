import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { Store } from '@ngrx/store';
import { resetErrors, setErrors } from 'app/common/errors.state';
import { MeasureHistogram } from 'app/measures/measures';
import { MeasureHistogramState } from 'app/person-filters-selector/measure-histogram.state';
import { NumberHistogram, CategoricalHistogramView, CategoricalHistogram } from 'app/utils/histogram-types';
import { environment } from 'environments/environment';
import { cloneDeep } from 'lodash';
import { ReplaySubject } from 'rxjs';

@Component({
    selector: 'gpf-person-filter',
    templateUrl: './person-filter.component.html',
    styleUrl: './person-filter.component.css',
    standalone: false
})
export class PersonFilterComponent implements OnInit, OnDestroy {
  @Input() public selectedMeasure: MeasureHistogram;
  @Input() public initialState: MeasureHistogramState;
  @Input() public isFamilyFilters: boolean;
  public localState: MeasureHistogramState;
  @Output() public updateState = new EventEmitter<MeasureHistogramState>();
  @Output() public updateHistogram = new EventEmitter<{ measureId: string, roles: string[] }>();
  public errors: string[] = [];
  public histogramErrors: string[] = [];
  private readonly maxBarCount = 25;

  // Refactor needed, not removal.
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);
  public imgPathPrefix = environment.imgPathPrefix;

  public constructor(
      protected store: Store
  ) { }

  public ngOnInit(): void {
    this.localState = cloneDeep(this.initialState);
    this.validateState();

    const histogram = this.selectedMeasure.histogram;
    if (this.isCategoricalHistogram(histogram)) {
      let barCount = 0;
      if (histogram.displayedValuesCount) {
        barCount = histogram.displayedValuesCount;
      } else if (histogram.displayedValuesPercent) {
        barCount = Math.floor(histogram.values.length / 100 * histogram.displayedValuesPercent);
      }
      if (barCount > this.maxBarCount) {
        this.switchCategoricalHistogramView('dropdown selector');
      }
    }
  }

  public ngOnDestroy(): void {
    let component = 'personFilters';
    if (this.isFamilyFilters) {
      component = 'familyFilters';
    }
    this.store.dispatch(resetErrors({componentId: component + `: ${this.selectedMeasure.measure}`}));
  }

  public updateRangeStart(range): void {
    this.localState.rangeStart = range as number;
    this.updateHistogramState();
  }

  public updateRangeEnd(range): void {
    this.localState.rangeEnd = range as number;
    this.updateHistogramState();
  }

  public get domainMin(): number {
    return (this.selectedMeasure.histogram as NumberHistogram).bins[0];
  }

  public get domainMax(): number {
    const lastIndex = (this.selectedMeasure.histogram as NumberHistogram).bins.length - 1;
    return (this.selectedMeasure.histogram as NumberHistogram).bins[lastIndex];
  }

  public replaceCategoricalValues(values: string[]): void {
    this.localState.values = values;
    this.updateHistogramState();
  }

  public replaceSelectedRoles(roles: string[]): void {
    this.localState.roles = roles;
    if (!roles.length) {
      roles = null;
    }
    this.updateHistogram.emit({ measureId: this.localState.measure, roles: roles });
  }

  private updateHistogramState(): void {
    this.validateState();
    this.updateState.emit(this.localState);
  }

  public switchCategoricalHistogramView(view: CategoricalHistogramView): void {
    if (view === this.localState.categoricalView) {
      return;
    }
    if (view === 'click selector' || view === 'dropdown selector') {
      this.localState.values = [];
    } else if (view === 'range selector' && this.isCategoricalHistogram(this.selectedMeasure.histogram)) {
      this.localState.values = this.selectedMeasure.histogram.values.map(v => v.name);
    }
    this.localState.categoricalView = view;
    this.updateHistogramState();
  }

  public isNumberHistogram(arg: object): arg is NumberHistogram {
    return arg instanceof NumberHistogram;
  }

  public isCategoricalHistogram(arg: object): arg is CategoricalHistogram {
    return arg instanceof CategoricalHistogram;
  }

  public setHistogramValidationErrors(errors: string[]): void {
    this.histogramErrors = errors;
    this.validateState();
  }


  private validateState(): void {
    this.errors = [];
    if (this.histogramErrors.length) {
      this.errors.push(...this.histogramErrors);
    }

    if (!this.localState) {
      return;
    }
    if (!this.localState.measure) {
      this.errors.push('Empty pheno measures are invalid.');
    }

    let component = 'personFilters';
    if (this.isFamilyFilters) {
      component = 'familyFilters';
    }

    if (this.errors.length) {
      this.store.dispatch(setErrors({
        errors: {
          componentId: component + `: ${this.selectedMeasure.measure}`, errors: cloneDeep(this.errors)
        }
      }));
    } else {
      this.store.dispatch(resetErrors({componentId: component + `: ${this.selectedMeasure.measure}`}));
    }
  }
}
