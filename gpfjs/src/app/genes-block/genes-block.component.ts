import { Component, Input, forwardRef, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryStateCollector } from '../query/query-state-provider'
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => GenesBlockComponent) }]
})
export class GenesBlockComponent extends QueryStateCollector {
  @Input() showAllTab = true;
  @ViewChild('tabset') ngbTabset;

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngAfterViewInit() {
    console.log(this.ngbTabset)
    this.stateRestoreService.state.subscribe(
      (state) => {
        if ("geneSymbols" in state) {
          this.ngbTabset.select("gene-symbols")
        }
        else if ("geneSet" in state) {
          this.ngbTabset.select("gene-sets")
        }
        else if ("geneWeights" in state) {
          this.ngbTabset.select("gene-weights")
        }
      }
    )
  }
}
