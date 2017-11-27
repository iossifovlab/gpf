import { Input, Component, OnInit, ViewChild, ViewEncapsulation, Output,
         EventEmitter, OnChanges, SimpleChanges, ChangeDetectorRef, forwardRef
       } from '@angular/core';
import { FormControl } from '@angular/forms';
import { GeneWeights, Partitions } from './gene-weights';
import { GeneWeightsService } from './gene-weights.service';
import { ReplaySubject }           from 'rxjs/ReplaySubject';
import { Observable }        from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';
import 'rxjs/add/operator/switchMap';
import 'rxjs/add/observable/of';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { StateRestoreService } from '../store/state-restore.service';
import { ConfigService } from '../config/config.service';

import { GeneWeightsState } from './gene-weights-store';

@Component({
  encapsulation: ViewEncapsulation.None,
  selector: 'gpf-gene-weights',
  templateUrl: './gene-weights.component.html',
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => GeneWeightsComponent)
  }]
})
export class GeneWeightsComponent extends QueryStateWithErrorsProvider implements OnInit {
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);
  private partitions: Observable<Partitions>;

  geneWeightsArray: GeneWeights[];

  rangesCounts: Observable<Array<number>>;
  private geneWeightsState = new GeneWeightsState();

  constructor(
    private geneWeightsService: GeneWeightsService,
    private changeDetectorRef: ChangeDetectorRef,
    private stateRestoreService: StateRestoreService,
    private config: ConfigService
  ) {
    super();

    this.partitions = this.rangeChanges
      .debounceTime(100)
      .distinctUntilChanged()
      .switchMap(([weight, internalRangeStart, internalRangeEnd]) => {
        return this.geneWeightsService.getPartitions(weight, internalRangeStart, internalRangeEnd);
      })
      .catch(error => {
        console.warn(error);
        return Observable.of(null);
      });

    this.rangesCounts = this.partitions.map(
      (partitions) => {
         return [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
  }

  private updateLabels() {
    this.rangeChanges.next([
      this.geneWeightsState.weight.weight,
      this.geneWeightsState.rangeStart,
      this.geneWeightsState.rangeEnd
    ]);
  }

  set selectedGeneWeights(selectedGeneWeights: GeneWeights) {
    this.geneWeightsState.weight = selectedGeneWeights;
    this.geneWeightsState.rangeStart = null;
    this.geneWeightsState.rangeEnd = null;
    this.geneWeightsState.domainMin = selectedGeneWeights.bins[0];
    this.geneWeightsState.domainMax =
      selectedGeneWeights.bins[selectedGeneWeights.bins.length - 1];
    this.updateLabels();
  }

  get selectedGeneWeights() {
    return this.geneWeightsState.weight;
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['geneWeights'] && state['geneWeights']['weight']) {
          for (let geneWeight of this.geneWeightsArray) {
            if (geneWeight.weight === state['geneWeights']['weight']) {
              this.selectedGeneWeights = geneWeight;
            }
          }
        }

        if (state['geneWeights'] && state['geneWeights']['rangeStart']) {
          this.rangeStart = state['geneWeights']['rangeStart'];
        }

        if (state['geneWeights'] && state['geneWeights']['rangeEnd']) {
          this.rangeEnd = state['geneWeights']['rangeEnd'];
        }
      });
  }

  ngOnInit() {

    this.geneWeightsService.getGeneWeights()
      .subscribe(geneWeights => {
          this.geneWeightsArray = geneWeights;
          this.selectedGeneWeights = geneWeights[0];

          this.restoreStateSubscribe();
      });
  }

  set rangeStart(range: number) {
    this.geneWeightsState.rangeStart = range;
    this.updateLabels();
  }

  get rangeStart() {
    return this.geneWeightsState.rangeStart;
  }

  set rangeEnd(range: number) {
    this.geneWeightsState.rangeEnd = range;
    this.updateLabels();
  }

  get rangeEnd() {
    return this.geneWeightsState.rangeEnd;
  }

  getState() {
    return this.validateAndGetState(this.geneWeightsState)
      .map(geneWeightsState => {

        return {
          geneWeights: {
            weight: geneWeightsState.weight.weight,
            rangeStart: geneWeightsState.rangeStart,
            rangeEnd: geneWeightsState.rangeEnd
          }
        };
      });
  }

  getDownloadLink(): string {
    return `${this.config.baseUrl}gene_weights/download/${this.selectedGeneWeights.weight}`;
  }
}
