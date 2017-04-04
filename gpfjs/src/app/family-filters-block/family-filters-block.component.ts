import { Component, OnInit, Input, forwardRef } from '@angular/core';
import { PhenoFilter } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => FamilyFiltersBlockComponent) }]
})
export class FamilyFiltersBlockComponent extends QueryStateCollector implements OnInit {
  @Input() phenoFilters: Array<PhenoFilter>;
  @Input() datasetId: string;

  constructor() {
    super();
  }

  ngOnInit() {
  }

}
