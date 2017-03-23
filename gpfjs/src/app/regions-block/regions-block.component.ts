import { Component, OnInit, forwardRef, ViewChild } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryStateCollector } from '../query/query-state-provider'
import { StateRestoreService } from '../store/state-restore.service'

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => RegionsBlockComponent) }]
})
export class RegionsBlockComponent extends QueryStateCollector {
  @ViewChild('tabset') ngbTabset;

  constructor(
    private store: Store<any>,
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngAfterViewInit() {
  this.stateRestoreService.state.subscribe(
    (state) => {
      if ("regions" in state) {
        this.ngbTabset.select("regions-filter")
      }
    }
  )
}
}
