import { Input, Component, OnInit, ViewChild, ViewEncapsulation, Output, EventEmitter, OnChanges, SimpleChanges, ChangeDetectorRef } from '@angular/core';
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

import { RANGE_CHANGE } from './gene-weights-store';

@Component({
  encapsulation: ViewEncapsulation.None,
  selector: 'gpf-gene-weights',
  templateUrl: './gene-weights.component.html'
})
export class GeneWeightsComponent {
  private rangeChanges = new Subject<Array<number >>();
  private partitions: Observable<Partitions>;

  private internalSelectedGeneWeights: GeneWeights;

  geneWeightsArray: GeneWeights[];
  private internalRangeStart: number;
  private internalRangeEnd: number;

  private rangesCounts: Array<number>;

  constructor(
    private geneWeightsService: GeneWeightsService,
    private changeDetectorRef: ChangeDetectorRef,
    private store: Store<any>
  )  {

  }

  set selectedGeneWeights(selectedGeneWeights: GeneWeights) {
    this.internalSelectedGeneWeights = selectedGeneWeights;
    this.rangeStart = selectedGeneWeights.min;
    this.rangeEnd = selectedGeneWeights.max;
  }

  get selectedGeneWeights() {
    return this.internalSelectedGeneWeights;
  }

  ngOnInit() {
    this.geneWeightsService.getGeneWeights().subscribe(
      (geneWeights) => {
        this.geneWeightsArray = geneWeights;
        this.selectedGeneWeights = geneWeights[0];
    });


    this.partitions = this.rangeChanges
      .debounceTime(100)
      .distinctUntilChanged()
      .switchMap(term => {
        this.store.dispatch({
          'type': RANGE_CHANGE,
          'payload': [this.selectedGeneWeights.weight, this.internalRangeStart, this.internalRangeEnd]
        });
        return this.geneWeightsService.getPartitions(this.selectedGeneWeights.weight, this.internalRangeStart, this.internalRangeEnd);
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
    if (!this.selectedGeneWeights
        || range > this.internalRangeEnd
        || range < 0
        || range === null) {
      return;
    }
    this.internalRangeStart = range;
    console.log("rangeStart", range);
    this.rangeChanges.next([this.internalRangeStart, this.internalRangeEnd]);
  }

  get rangeStart() {
    return this.internalRangeStart;
  }

  set rangeEnd(range: number) {
    if (!this.selectedGeneWeights
        || range > this.selectedGeneWeights.max
        || range < this.internalRangeStart
        || range === null) {
      return;
    }
    this.internalRangeEnd = range;
    console.log("rangeEnd", this.internalRangeStart, this.internalRangeEnd);
    this.rangeChanges.next([this.internalRangeStart, this.internalRangeEnd]);
  }

  get rangeEnd() {
    return this.internalRangeEnd;
  }
}
