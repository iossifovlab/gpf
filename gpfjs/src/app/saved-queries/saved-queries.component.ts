import { Component, OnInit, OnChanges } from '@angular/core';
import { QueryService } from '../query/query.service';

export class UserSavedQuery {
  constructor(
    public name: string,
    public description: string,
    public page: string,
    public uuid: string,
    public url: string
  ) {}
}

@Component({
  selector: 'gpf-saved-queries',
  templateUrl: './saved-queries.component.html',
  styleUrls: ['./saved-queries.component.css']
})
export class SavedQueriesComponent implements OnInit {

  genotypeQueries: Array<UserSavedQuery>;
  phenotypeQueries: Array<UserSavedQuery>;
  phenotoolQueries: Array<UserSavedQuery>;
  enrichmentQueries: Array<UserSavedQuery>;

  constructor(
    private queryService: QueryService,
  ) {}

  ngOnInit() {
    this.updateQueries();
  }

  updateQueries() {
    this.queryService.collectUserSavedQueries().subscribe(response => {
      const queries = response['queries'].map(query => {
        return new UserSavedQuery(
          query.name,
          query.description,
          query.page,
          query.query_uuid,
          this.queryService.getLoadUrl(query.query_uuid)
        );
      });

      this.genotypeQueries = queries.filter(query => query.page === 'genotype');
      this.phenotypeQueries = queries.filter(query => query.page === 'phenotype');
      this.phenotoolQueries = queries.filter(query => query.page === 'phenotool');
      this.enrichmentQueries = queries.filter(query => query.page === 'enrichment');
    });
  }
}
