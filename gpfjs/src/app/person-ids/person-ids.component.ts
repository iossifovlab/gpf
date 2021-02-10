import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { IsNotEmpty } from 'class-validator';

export class PersonIds {
  @IsNotEmpty()
  personIds = '';
}

@Component({
  selector: 'gpf-person-ids',
  templateUrl: './person-ids.component.html',
  styleUrls: ['./person-ids.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => PersonIdsComponent)
  }]
})
export class PersonIdsComponent extends QueryStateWithErrorsProvider implements OnInit {

  personIds = new PersonIds();

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
        if (state['personIds']) {
          this.personIds.personIds = state['personIds'].join('\n');
        }
      }
    );
  }

  getState() {
    return this.validateAndGetState(this.personIds).map(personIds => {
      const result = personIds.personIds
          .split(/[,\s]/)
          .filter(s => s !== '');
        if (result.length === 0) {
          return {};
        }
        return { personIds: result };
      });
  }

}
