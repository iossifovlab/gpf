import { Input, Component, OnInit, ViewChild, ViewEncapsulation, Output,
         EventEmitter, OnChanges, SimpleChanges, ChangeDetectorRef, forwardRef
       } from '@angular/core';
import { FormControl } from '@angular/forms';
import { GeneWeights, Partitions } from './gene-weights';
import { GeneWeightsService } from './gene-weights.service';
import { Subject }           from 'rxjs/Subject';
import { Observable }        from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/debounceTime';
import 'rxjs/add/operator/distinctUntilChanged';
import 'rxjs/add/operator/switchMap';
import 'rxjs/add/observable/of';
import { Store } from '@ngrx/store';
import { QueryStateProvider } from '../query/query-state-provider'
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { StateRestoreService } from '../store/state-restore.service'

import { GeneWeightsState, GENE_WEIGHTS_CHANGE, GENE_WEIGHTS_INIT,
         GENE_WEIGHTS_RANGE_START_CHANGE, GENE_WEIGHTS_RANGE_END_CHANGE

 } from './gene-weights-store';

@Component({
  encapsulation: ViewEncapsulation.None,
  selector: 'gpf-gene-weights',
  templateUrl: './gene-weights.component.html',
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GeneWeightsComponent) }]
})
export class GeneWeightsComponent extends QueryStateProvider {
  private rangeChanges = new Subject<[string, number, number]>();
  private partitions: Observable<Partitions>;

  private internalSelectedGeneWeights: GeneWeights;

  geneWeightsArray: GeneWeights[];
  private internalRangeStart: number;
  private internalRangeEnd: number;

  private rangesCounts: Array<number>;
  private geneWeightsState: Observable<[GeneWeightsState, boolean, ValidationError[]]>;

  errors: string[];
  flashingAlert = false;


  constructor(
    private geneWeightsService: GeneWeightsService,
    private changeDetectorRef: ChangeDetectorRef,
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  )  {
    super();
    this.geneWeightsState = toObservableWithValidation(GeneWeightsState, this.store.select('geneWeights'));
    this.geneWeightsState.subscribe(
      ([geneWeightsState, isValid, validationErrors]) => {
        this.errors = validationErrorsToStringArray(validationErrors);

        this.internalSelectedGeneWeights = geneWeightsState.weight;
        this.internalRangeStart = geneWeightsState.rangeStart;
        this.internalRangeEnd = geneWeightsState.rangeEnd;

        if (isValid) {
          this.rangeChanges.next([geneWeightsState.weight.weight, this.internalRangeStart, this.internalRangeEnd]);
        }
      }
    );
  }

  set selectedGeneWeights(selectedGeneWeights: GeneWeights) {
    this.store.dispatch({
      'type': GENE_WEIGHTS_CHANGE,
      'payload': [selectedGeneWeights, selectedGeneWeights.min, selectedGeneWeights.max]
    });
  }

  get selectedGeneWeights() {
    return this.internalSelectedGeneWeights;
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name).subscribe(
      (state) => {
        if (state['geneWeights'] && state['geneWeights']['weight']) {
          for (let geneWeight of this.geneWeightsArray) {
            if (geneWeight.weight == state['geneWeights']['weight']) {
              this.store.dispatch({
                'type': GENE_WEIGHTS_CHANGE,
                'payload': [geneWeight, geneWeight.min, geneWeight.max]
              });
            }
          }
        }

        if (state['geneWeights'] && state['geneWeights']['rangeStart']) {
          this.store.dispatch({
            'type': GENE_WEIGHTS_RANGE_START_CHANGE,
            'payload': state['geneWeights']['rangeStart']
          });
        }

        if (state['geneWeights'] && state['geneWeights']['rangeEnd']) {
          this.store.dispatch({
            'type': GENE_WEIGHTS_RANGE_END_CHANGE,
            'payload': state['geneWeights']['rangeEnd']
          });
        }
      }
    )
  }

  ngOnInit() {
    this.store.dispatch({
      'type': GENE_WEIGHTS_INIT,
    });

    this.geneWeightsService.getGeneWeights().subscribe(
      (geneWeights) => {
        this.geneWeightsArray = geneWeights;
        this.selectedGeneWeights = geneWeights[0];

        this.restoreStateSubscribe();
    });


    this.partitions = this.rangeChanges
      .debounceTime(100)
      .distinctUntilChanged()
      .switchMap(([weight, internalRangeStart, internalRangeEnd]) => {
        return this.geneWeightsService.getPartitions(weight, internalRangeStart, internalRangeEnd);
      })
      .catch(error => {
        console.log(error);
        return null;
      });

    this.partitions.subscribe(
      (partitions) => {
        this.rangesCounts = [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
  }


  set rangeStart(range: number) {
    this.store.dispatch({
      'type': GENE_WEIGHTS_RANGE_START_CHANGE,
      'payload': range
    });
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  set rangeEnd(range: number) {
    this.store.dispatch({
      'type': GENE_WEIGHTS_RANGE_END_CHANGE,
      'payload': range
    });
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }

  getState() {
    return this.geneWeightsState.take(1).map(
      ([geneWeightsState, isValid, validationErrors]) => {
        if (!isValid) {
          this.flashingAlert = true;
          setTimeout(()=>{ this.flashingAlert = false }, 1000)

           throw "invalid geneWeights state"
        }
        return { geneWeights: {
          weight: geneWeightsState.weight.weight,
          rangeStart: geneWeightsState.rangeStart,
          rangeEnd: geneWeightsState.rangeEnd
        }}
    });
  }
}
