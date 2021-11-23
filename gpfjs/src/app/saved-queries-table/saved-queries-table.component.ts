import { Component, Input } from '@angular/core';
import { UserSavedQuery } from '../saved-queries/saved-queries.component';
import { QueryService } from '../query/query.service';

@Component({
  selector: 'gpf-saved-queries-table',
  templateUrl: './saved-queries-table.component.html',
  styleUrls: ['./saved-queries-table.component.css']
})
export class SavedQueriesTableComponent {
  @Input() public queries: Array<UserSavedQuery>;

  constructor(
    private queryService: QueryService
  ) {}

  public deleteQuery(uuid: string): void {
    this.queries = this.queries.filter(query => query.uuid !== uuid);
    this.queryService.deleteQuery(uuid).subscribe();
  }

  copyToClipboard(item) {
    document.addEventListener('copy', (e: ClipboardEvent) => {
      e.clipboardData.setData('text/plain', (item));
      e.preventDefault();
      document.removeEventListener('copy', null);
    });
    document.execCommand('copy');
  }
}
