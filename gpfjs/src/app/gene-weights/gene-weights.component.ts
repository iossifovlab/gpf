import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { GeneWeights, Partitions, GeneWeightsLocalState } from './gene-weights';
import { GeneWeightsService } from './gene-weights.service';
// tslint:disable-next-line:import-blacklist
import { ReplaySubject ,  Observable } from 'rxjs';

import { Store, Select } from '@ngxs/store';
import { ConfigService } from '../config/config.service';

import { SetGeneWeight, SetHistogramValues, GeneWeightsState, GeneWeightsModel } from './gene-weights.state';
import { validate } from 'class-validator';

@Component({
  encapsulation: ViewEncapsulation.None, // TODO: What is this?
  selector: 'gpf-gene-weights',
  templateUrl: './gene-weights.component.html',
})
export class GeneWeightsComponent implements OnInit {
  private rangeChanges = new ReplaySubject<[string, number, number]>(1);
  private partitions: Observable<Partitions>;

  geneWeightsArray: GeneWeights[];
  rangesCounts: Observable<Array<number>>;
  geneWeightsLocalState = new GeneWeightsLocalState();

  @Select(GeneWeightsState) state$: Observable<GeneWeightsModel>;
  errors: Array<string> = [];

  constructor(
    private store: Store,
    private geneWeightsService: GeneWeightsService,
    private config: ConfigService,
  ) {
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

    this.rangesCounts = this.partitions.map((partitions) => {
       return [partitions.leftCount, partitions.midCount, partitions.rightCount];
    });
  }

  ngOnInit() {
    this.geneWeightsService.getGeneWeights()
      .subscribe(geneWeights => {
        this.geneWeightsArray = geneWeights;
        this.selectedGeneWeights = geneWeights[0];
      });

    this.store.selectOnce(state => state.geneWeightsState).subscribe(state => {
      // restore state
      if (state.weight) {
        for (const geneWeight of this.geneWeightsArray) {
          if (geneWeight.weight === state.weight) {
            this.selectedGeneWeights = geneWeight;
          }
        }
      }

      if (state.rangeStart) {
        this.rangeStart = state.rangeStart;
      }

      if (state.rangeEnd) {
        this.rangeEnd = state.rangeEnd;
      }
    });

    this.state$.subscribe(state => {
      // validate for errors
      validate(this).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  private updateLabels() {
    this.rangeChanges.next([
      this.geneWeightsLocalState.weight.weight,
      this.rangeStart,
      this.rangeEnd
    ]);
  }

  updateHistogramState() {
    this.updateLabels();
    this.store.dispatch(new SetHistogramValues(
      this.geneWeightsLocalState.rangeStart,
      this.geneWeightsLocalState.rangeEnd,
    ));
  }

  get selectedGeneWeights() {
    return this.geneWeightsLocalState.weight;
  }

  set selectedGeneWeights(selectedGeneWeights: GeneWeights) {
    this.geneWeightsLocalState.weight = selectedGeneWeights;
    this.rangeStart = null;
    this.rangeEnd = null;
    this.changeDomain(selectedGeneWeights);
    this.updateLabels();
    this.store.dispatch(new SetGeneWeight(this.geneWeightsLocalState.weight));
  }

  set rangeStart(range: number) {
    this.geneWeightsLocalState.rangeStart = range;
    this.updateHistogramState();
  }

  get rangeStart() {
    return this.geneWeightsLocalState.rangeStart;
  }

  set rangeEnd(range: number) {
    this.geneWeightsLocalState.rangeEnd = range;
    this.updateHistogramState();
  }

  get rangeEnd() {
    return this.geneWeightsLocalState.rangeEnd;
  }

  getDownloadLink(): string {
    return `${this.config.baseUrl}gene_weights/download/${this.selectedGeneWeights.weight}`;
  }

  changeDomain(weights: GeneWeights) {
    if (weights.domain !== null) {
      this.geneWeightsLocalState.domainMin = weights.domain[0];
      this.geneWeightsLocalState.domainMax = weights.domain[1];
    } else {
      this.geneWeightsLocalState.domainMin = weights.bins[0];
      this.geneWeightsLocalState.domainMax = weights.bins[weights.bins.length - 1];
    }
  }
}
