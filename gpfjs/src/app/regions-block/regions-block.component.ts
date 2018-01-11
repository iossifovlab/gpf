import { Component, OnInit, forwardRef, ViewChild, AfterViewInit } from '@angular/core';
import { QueryStateCollector } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
  providers: [{
    provide: QueryStateCollector,
    useExisting: forwardRef(() => RegionsBlockComponent)
  }]
})
export class RegionsBlockComponent extends QueryStateCollector implements AfterViewInit {
  @ViewChild('tabset') ngbTabset;

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngAfterViewInit() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if ('regions' in state) {
          this.ngbTabset.select('regions-filter');
        }
      });
  }
}
