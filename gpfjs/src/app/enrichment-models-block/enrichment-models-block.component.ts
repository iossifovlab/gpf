import { Component, forwardRef, Input } from '@angular/core';

import { QueryStateCollector } from '../query/query-state-provider';

@Component({
  selector: 'gpf-enrichment-models-block',
  templateUrl: './enrichment-models-block.component.html',
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => EnrichmentModelsBlockComponent) }]
})
export class EnrichmentModelsBlockComponent extends QueryStateCollector  {
  @Input()
  private selectedDatasetId: string;
}
