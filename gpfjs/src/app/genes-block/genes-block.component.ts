import { Component, Input, forwardRef } from '@angular/core';
import { Store } from '@ngrx/store';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => GenesBlockComponent) }]
})
export class GenesBlockComponent extends QueryStateCollector {
  @Input() showAllTab = true;

  constructor(
    private store: Store<any>
  ) {
    super();
  }
}
