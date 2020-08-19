import { Component, Input, forwardRef, ViewChild, AfterViewInit } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-genes-block',
  templateUrl: './genes-block.component.html',
  styleUrls: ['./genes-block.component.css'],
  providers: [{provide: QueryStateCollector, useExisting: forwardRef(() => GenesBlockComponent) }]
})
export class GenesBlockComponent extends QueryStateCollector implements AfterViewInit {
  @Input() showAllTab = true;
  @ViewChild('nav') ngbNav;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if ('geneSymbols' in state) {
          this.ngbNav.select('geneSymbols');
        } else if ('geneSet' in state) {
          this.ngbNav.select('geneSets');
        } else if ('geneWeights' in state) {
          this.ngbNav.select('geneWeights');
        }
      }
    );
  }
}
