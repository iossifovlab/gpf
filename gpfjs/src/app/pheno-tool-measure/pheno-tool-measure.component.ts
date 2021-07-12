import { Component, OnInit, ElementRef, QueryList, ViewChildren } from '@angular/core';
// tslint:disable-next-line:import-blacklist
import { Observable, ReplaySubject } from 'rxjs';
import { ContinuousMeasure } from '../measures/measures';
import { MeasuresService } from '../measures/measures.service';
import { DatasetsService } from '../datasets/datasets.service';
import { IsNotEmpty, validate } from 'class-validator';
import { Store, Select } from '@ngxs/store';
import {
  SetPhenoToolMeasure, PhenoToolMeasureModel, PhenoToolMeasureState
} from './pheno-tool-measure.state';
import { switchMap } from 'rxjs/operators';

interface Regression {
  display_name: string;
  instrument_name: string;
  measure_name: string;
}

@Component({
  selector: 'gpf-pheno-tool-measure',
  templateUrl: './pheno-tool-measure.component.html',
  styleUrls: ['./pheno-tool-measure.component.css'],
})
export class PhenoToolMeasureComponent implements OnInit {
  @ViewChildren('checkboxes') inputs: QueryList<ElementRef>;

  @IsNotEmpty()
  selectedMeasure: ContinuousMeasure = null;
  normalizeBy: Regression[] = new Array<Regression>();

  measuresLoaded$ = new ReplaySubject<Array<ContinuousMeasure>>();

  regressions: Object = {};

  @Select(PhenoToolMeasureState) state$: Observable<PhenoToolMeasureModel>;
  errors: Array<string> = [];

  constructor(
    private store: Store,
    private measuresService: MeasuresService,
    private datasetsService: DatasetsService,
  ) { }

  ngOnInit() {
    Observable.combineLatest(
      this.store.selectOnce(PhenoToolMeasureState), this.measuresLoaded$).take(1)
      .subscribe(([state, measures]) => {
        if (state.measureId) {
          this.selectedMeasure = measures.find(m => m.name === state.measureId);
        }
        this.normalizeBy = state.normalizeBy.length ? state.normalizeBy : [];
      });

    this.datasetsService.getSelectedDataset().subscribe(dataset => {
      if (dataset.phenotypeData) {
        this.measuresService.getRegressions(dataset.id).subscribe(
          res => { this.regressions = res });
      } else {
        this.regressions = {};
      }
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  get measure() {
    return this.selectedMeasure;
  }

  set measure(value) {
    this.selectedMeasure = value;
    if (this.selectedMeasure) {
      this.normalizeBy = this.normalizeBy.filter(
        (reg) => `${reg.instrument_name}.${reg.measure_name}` !== this.selectedMeasure?.name
      );
    }
    this.updateState();
  }

  updateState() {
    this.store.dispatch(new SetPhenoToolMeasure(
      this.selectedMeasure?.name, this.normalizeBy,
    ))
  }

  measuresUpdate(measures: Array<ContinuousMeasure>) {
    this.measuresLoaded$.next(measures);
  }

  onNormalizeByChange(value: Regression, event): void {
    if (event.target.checked) {
      if (!this.normalizeBy.some((reg) => reg.measure_name === value.measure_name)) {
        this.normalizeBy.push(value);
      }
    } else {
      this.normalizeBy = this.normalizeBy.filter(
        reg => reg.measure_name !== value.measure_name
      );
    }
    this.updateState();
  }

  getRegressionNames() {
    return Object.getOwnPropertyNames(this.regressions);
  }

  isNormalizedBy(reg: string): boolean {
    return this.normalizeBy.some(norm => norm.measure_name === reg);
  }
}
