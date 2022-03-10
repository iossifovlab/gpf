import { Component, OnInit } from '@angular/core';
import { AgpSingleViewConfig } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { AutismGeneProfilesService  } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { take } from 'rxjs/operators';
import { Store } from '@ngxs/store';
import { QueryService } from 'app/query/query.service';
import { AutismGeneProfileSingleViewComponent } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view.component';
import { AgpTableConfig } from 'app/autism-gene-profiles-table/autism-gene-profiles-table';
import { AgpTableService } from 'app/autism-gene-profiles-table/autism-gene-profiles-table.service';

@Component({
  selector: 'gpf-autism-gene-profiles-block',
  templateUrl: './autism-gene-profiles-block.component.html',
  styleUrls: ['./autism-gene-profiles-block.component.css']
})
export class AutismGeneProfilesBlockComponent implements OnInit {
  public agpTableConfig: AgpTableConfig;
  public agpTableSortBy: string;
  public agpSingleViewConfig: AgpSingleViewConfig;

  public constructor(
    private agpTableService: AgpTableService,
    private autismGeneProfilesService: AutismGeneProfilesService,
    private queryService: QueryService,
    private store: Store
  ) { }

  public ngOnInit(): void {
    this.agpTableService.getConfig().pipe(take(1)).subscribe(config => {
      this.agpTableConfig = config;
      this.agpTableSortBy = this.findFirstAgpSortableCategory(config);
    });
    this.autismGeneProfilesService.getConfig().pipe(take(1)).subscribe(config => {
      this.agpSingleViewConfig = config;
    });
  }

  private findFirstAgpSortableCategory(agpTableConfig: AgpTableConfig): string {
    return agpTableConfig.columns.filter(column => column.sortable)[0].id;
  }

  public goToQueryEventHandler($event: { geneSymbol: string; statisticId: string }): void {
    const tokens: string[] = $event.statisticId.split('.');
    const datasetId = tokens[0];
    const personSet = this.agpSingleViewConfig.datasets
      .find(ds => ds.id === datasetId).personSets
      .find(ps => ps.id === tokens[1]);
    const statistic = personSet.statistics.find(st => st.id === tokens[2]);
    AutismGeneProfileSingleViewComponent.goToQuery(this.store, this.queryService, $event.geneSymbol, personSet, datasetId, statistic);
  }
}
