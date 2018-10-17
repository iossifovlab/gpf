import { Component, Input, OnInit, forwardRef } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider'

@Component({
  selector: 'gpf-pheno-tool-genotype-block',
  templateUrl: './pheno-tool-genotype-block.component.html',
  styleUrls: ['./pheno-tool-genotype-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => PhenoToolGenotypeBlockComponent) }]
})
export class PhenoToolGenotypeBlockComponent extends QueryStateCollector  implements OnInit {

  @Input()
  hasCNV = false;

  constructor() {
    super(); 
  }

  ngOnInit() {
  }

}
