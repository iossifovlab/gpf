import { Component, Input, forwardRef } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { QueryStateCollector } from '../query/query-state-provider';


@Component({
  selector: 'gpf-missense-scores-block',
  templateUrl: './missense-scores-block.component.html',
  styleUrls: ['./missense-scores-block.component.css'],
  providers: [{provide: QueryStateCollector,
               useExisting: forwardRef(() => MissenseScoresBlockComponent) }]
})
export class MissenseScoresBlockComponent extends QueryStateCollector {
  @Input() datasetConfig: Dataset;
}
