import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { FamilyIds } from './family-ids';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => FamilyIdsComponent)
  }]
})
export class FamilyIdsComponent extends QueryStateWithErrorsProvider implements OnInit {

  familyIds = new FamilyIds();

  constructor(
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  ngOnInit() {
    this.stateRestoreService
      .getState(this.constructor.name)
      .take(1)
      .subscribe(
      (state) => {
        if (state['familyIds']) {
          this.familyIds.familyIds = state['familyIds'].join('\n');
        }
      }
    );
  }

  getState() {
    return this.validateAndGetState(this.familyIds).map(familyIds => {
        let result = familyIds.familyIds
          .split(/[,\s]/)
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }

        return { familyIds: result };
      });
  }

}
