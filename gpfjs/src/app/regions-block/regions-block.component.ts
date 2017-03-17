import { Component, OnInit, forwardRef } from '@angular/core';
import { REGIONS_BLOCK_TAB_DESELECT } from '../store/common';
import { Store } from '@ngrx/store';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => RegionsBlockComponent) }]
})
export class RegionsBlockComponent extends QueryStateCollector implements OnInit {

  constructor(
    private store: Store<any>
  ) {
    super();
  }

  ngOnInit() {
  }

  onTabChange(event) {
    this.store.dispatch({
      'type': REGIONS_BLOCK_TAB_DESELECT,
      'payload': event.activeId
    });
  }

}
