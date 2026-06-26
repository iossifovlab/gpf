import { Component, Input, inject } from '@angular/core';
import { UserSavedQuery } from '../user-profile/user-profile.component';
import { QueryService } from '../query/query.service';

@Component({
  selector: 'gpf-saved-queries-table',
  templateUrl: './saved-queries-table.component.html',
  styleUrls: ['./saved-queries-table.component.css'],
  standalone: false
})
export class SavedQueriesTableComponent {
  private queryService = inject(QueryService);

  @Input() public queries: Array<UserSavedQuery>;

  public deleteQuery(uuid: string): void {
    this.queries = this.queries.filter(query => query.uuid !== uuid);
    this.queryService.deleteQuery(uuid).subscribe();
  }
}
