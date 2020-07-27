import { Component, OnInit, forwardRef, ElementRef, QueryList, ViewChildren } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
// tslint:disable-next-line:import-blacklist
import { Observable, ReplaySubject } from 'rxjs';
import { PhenoToolMeasure } from './pheno-tool-measure';
import { StateRestoreService } from '../store/state-restore.service';
import { ContinuousMeasure } from '../measures/measures';
import { MeasuresService } from '../measures/measures.service';
import { DatasetsService } from '../datasets/datasets.service';

@Component({
  selector: 'gpf-pheno-tool-measure',
  templateUrl: './pheno-tool-measure.component.html',
  styleUrls: ['./pheno-tool-measure.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PhenoToolMeasureComponent)
  }]
})
export class PhenoToolMeasureComponent extends QueryStateWithErrorsProvider implements OnInit {
  @ViewChildren('checkboxes') inputs: QueryList<ElementRef>;

  phenoToolMeasure = new PhenoToolMeasure();

  measuresLoaded$ = new ReplaySubject<Array<ContinuousMeasure>>();

  regressions: Object = {};

  constructor(
    private stateRestoreService: StateRestoreService,
    private measuresService: MeasuresService,
    private datasetsService: DatasetsService
  ) {
    super();
  }

  ngOnInit() {
    Observable.combineLatest(
      this.stateRestoreService.getState(this.constructor.name),
      this.measuresLoaded$)
      .take(1)
      .subscribe(([state, measures]) => {
        if (state['measureId'] && state['normalizeBy']) {
          this.phenoToolMeasure.measure =
            measures.find(m => m.name === state['measureId']);

          this.phenoToolMeasure.normalizeBy = state['normalizeBy'];
        }
      });

    this.datasetsService.getSelectedDataset().subscribe(
      dataset => {
        if (dataset.phenotypeData) {
          this.measuresService.getRegressions(dataset.id).subscribe(
            res => { this.regressions = res; });
        } else {
          this.regressions = {};
        }
      }
    );
  }

  getState() {
    return this.validateAndGetState(this.phenoToolMeasure)
      .map(state => ({
        measureId: state.measure.name,
        normalizeBy: state.normalizeBy
      }));
  }

  measuresUpdate(measures: Array<ContinuousMeasure>) {
    this.measuresLoaded$.next(measures);
  }

  onNormalizeByChange(value: any, event): void {
    if (event.target.checked) {
      if (this.phenoToolMeasure.normalizeBy.indexOf(value) === -1) {
        this.phenoToolMeasure.normalizeBy.push(value);
      }
    } else {
      if (this.phenoToolMeasure.normalizeBy.indexOf(value) !== -1) {
        this.phenoToolMeasure.normalizeBy =
          this.phenoToolMeasure.normalizeBy.filter(v => v !== value);
      }
    }
  }

  getRegressionNames() {
    return Object.getOwnPropertyNames(this.regressions);
  }

  uncheckCheckboxes(event) {
    this.inputs.forEach((directive, index) => {
      directive.nativeElement.checked = false;
    });
  }
}
