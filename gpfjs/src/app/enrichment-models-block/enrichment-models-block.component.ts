import { Component, OnInit, forwardRef } from '@angular/core';

import { IdDescription } from '../common/iddescription';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-enrichment-models-block',
  templateUrl: './enrichment-models-block.component.html',
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => EnrichmentModelsBlockComponent) }]
})
export class EnrichmentModelsBlockComponent extends QueryStateCollector  {

}
