import { Component, OnInit, forwardRef } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => RegionsBlockComponent) }]
})
export class RegionsBlockComponent extends QueryStateCollector {

  constructor(
    private store: Store<any>
  ) {
    super();
  }
}
