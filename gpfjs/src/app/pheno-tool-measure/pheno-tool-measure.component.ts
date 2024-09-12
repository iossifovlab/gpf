import { Component, OnInit, ElementRef, QueryList, ViewChildren, ViewChild } from '@angular/core';
// eslint-disable-next-line no-restricted-imports
import { combineLatest, of, ReplaySubject } from 'rxjs';
import { ContinuousMeasure } from '../measures/measures';
import { MeasuresService } from '../measures/measures.service';
import { IsNotEmpty } from 'class-validator';
import { Store } from '@ngrx/store';
import { selectPhenoToolMeasure, PhenoToolMeasureState, setPhenoToolMeasure } from './pheno-tool-measure.state';
import { switchMap, take } from 'rxjs/operators';
import { Dataset } from 'app/datasets/datasets';
import { PhenoMeasureSelectorComponent } from 'app/pheno-measure-selector/pheno-measure-selector.component';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { DatasetsService } from 'app/datasets/datasets.service';
import { ComponentValidator } from 'app/common/component-validator';

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
export class PhenoToolMeasureComponent extends ComponentValidator implements OnInit {
  @ViewChildren('checkboxes') public inputs: QueryList<ElementRef>;

  @IsNotEmpty({message: 'Please select a measure.'})
  public selectedMeasure: ContinuousMeasure = null;
  public normalizeBy: Regression[] = new Array<Regression>();

  public measuresLoaded$ = new ReplaySubject<Array<ContinuousMeasure>>();
  @ViewChild(PhenoMeasureSelectorComponent) private measureSelectorComponent: PhenoMeasureSelectorComponent;

  public regressions: object = {};
  public regressionNames: string[] = [];

  public dataset: Dataset;

  public constructor(
    protected store: Store,
    private measuresService: MeasuresService,
    private datasetsService: DatasetsService
  ) {
    super(store, 'phenoToolMeasure', selectPhenoToolMeasure);
  }

  public ngOnInit(): void {
    super.ngOnInit();

    this.store.select(selectDatasetId).pipe(
      take(1),
      switchMap(selectedDatasetIdState => this.datasetsService.getDataset(selectedDatasetIdState)),
      switchMap(dataset => {
        if (!dataset) {
          return;
        }
        this.dataset = dataset;
        if (this.dataset?.phenotypeData) {
          return this.measuresService.getRegressions(this.dataset.id).pipe(take(1));
        } else {
          return of();
        }
      })).subscribe({
      next: (res) => {
        if (res) {
          this.regressions = res;
          this.regressionNames = Object.getOwnPropertyNames(this.regressions);
        }
      },
      error: () => {
      // no regressions found in backend
      // empty error handling block to prevent 404 error showing up in the pheno tool
      }
    });


    combineLatest([this.store.select(selectPhenoToolMeasure), this.measuresLoaded$]).pipe(take(1))
      .subscribe(async([selectPhenoToolMeasureState, measures]: [PhenoToolMeasureState, ContinuousMeasure[]]) => {
        if (selectPhenoToolMeasureState.measureId) {
          this.selectedMeasure = measures.find(m => m.name === selectPhenoToolMeasureState.measureId);
          await this.waitForSelectorComponent();
          this.measureSelectorComponent.selectMeasure(this.selectedMeasure, false);
        }
        this.normalizeBy = selectPhenoToolMeasureState.normalizeBy.length
          ? selectPhenoToolMeasureState.normalizeBy as Regression[] : [];
        this.updateState();
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

  public get measure(): ContinuousMeasure {
    return this.selectedMeasure;
  }

  public set measure(value) {
    this.selectedMeasure = value;
    if (this.selectedMeasure) {
      this.normalizeBy = this.normalizeBy.filter(
        (reg) => `${reg.instrument_name}.${reg.measure_name}` !== this.selectedMeasure?.name
      );
    }
    this.updateState();
  }

  public updateState(): void {
    this.store.dispatch(setPhenoToolMeasure({
      phenoToolMeasure: {
        measureId: this.selectedMeasure?.name,
        normalizeBy: this.normalizeBy
      }
    }));
  }

  public measuresUpdate(measures: Array<ContinuousMeasure>): void {
    this.measuresLoaded$.next(measures);
  }

  public onNormalizeByChange(value: Regression, event): void {
    if (event.target.checked) {
      if (!this.normalizeBy.some((reg) => reg.measure_name === value.measure_name)) {
        this.normalizeBy = [...this.normalizeBy, value];
      }
    } else {
      this.normalizeBy = this.normalizeBy.filter(
        reg => reg.measure_name !== value.measure_name
      );
    }
    this.updateState();
  }

  public isNormalizedBy(reg: string): boolean {
    return this.normalizeBy.some(norm => norm.measure_name === reg);
  }

  public clearCheckbox(): void {
    this.inputs.forEach(checkbox => {
      checkbox.nativeElement.checked = false;
      checkbox.nativeElement.dispatchEvent(new Event('change'));
    });
  }
}
