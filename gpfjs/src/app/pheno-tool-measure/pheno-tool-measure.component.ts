import { Component, OnInit, ElementRef, QueryList, ViewChildren, ViewChild } from '@angular/core';
// eslint-disable-next-line no-restricted-imports
import { combineLatest, ReplaySubject } from 'rxjs';
import { ContinuousMeasure } from '../measures/measures';
import { MeasuresService } from '../measures/measures.service';
import { DatasetsService } from '../datasets/datasets.service';
import { IsNotEmpty } from 'class-validator';
import { Store } from '@ngxs/store';
import { SetPhenoToolMeasure, PhenoToolMeasureState } from './pheno-tool-measure.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { take } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';

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
export class PhenoToolMeasureComponent extends StatefulComponent implements OnInit {
  @ViewChildren('checkboxes') inputs: QueryList<ElementRef>;

  @IsNotEmpty({message: 'Please select a measure.'})
  selectedMeasure: ContinuousMeasure = null;
  normalizeBy: Regression[] = new Array<Regression>();

  measuresLoaded$ = new ReplaySubject<Array<ContinuousMeasure>>();
  @ViewChild(PhenoMeasureSelectorComponent) private measureSelectorComponent: PhenoMeasureSelectorComponent;

  regressions: Object = {};
  regressionNames: string[] = [];

  public dataset: Dataset;

  constructor(
    protected store: Store,
    private measuresService: MeasuresService,
    private datasetsService: DatasetsService,
  ) {
    super(store, PhenoToolMeasureState, 'phenoToolMeasure');
  }

  public ngOnInit() {
    super.ngOnInit();

    this.dataset = this.datasetsService.getSelectedDataset();
    if (this.dataset?.phenotypeData) {
      this.measuresService.getRegressions(this.dataset.id).pipe(take(1)).subscribe(res => {
        this.regressions = res;
        this.regressionNames = Object.getOwnPropertyNames(this.regressions);
      }, () => {
        // no regressions found in backend
        // empty error handling block to prevent 404 error showing up in the pheno tool
      });
    }

    combineLatest([this.store.selectOnce(PhenoToolMeasureState), this.measuresLoaded$]).pipe(take(1))
      .subscribe(async ([state, measures]) => {
        if (state.measureId) {
          this.selectedMeasure = measures.find(m => m.name === state.measureId);
          await this.waitForSelectorComponent();
          this.measureSelectorComponent.selectMeasure(this.selectedMeasure, false);
        }
        this.normalizeBy = state.normalizeBy.length ? state.normalizeBy : [];
        this.updateState();
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

  isNormalizedBy(reg: string): boolean {
    return this.normalizeBy.some(norm => norm.measure_name === reg);
  }

  public clearCheckbox(): void {
    this.inputs.forEach(checkbox => {
      checkbox.nativeElement.checked = false;
      checkbox.nativeElement.dispatchEvent(new Event("change"));
    });
  }
}
