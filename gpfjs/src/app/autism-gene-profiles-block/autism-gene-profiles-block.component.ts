import { Component, OnInit } from '@angular/core';
import {
  AgpDataset,
  AgpGeneSetsCategory,
  AgpGenomicScoresCategory,
  AgpSingleViewConfig} from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { map, take } from 'rxjs/operators';
import { Store } from '@ngxs/store';
import { QueryService } from 'app/query/query.service';
import { AgpColumn, AgpTableConfig } from 'app/autism-gene-profiles-table/autism-gene-profiles-table';
import { AgpTableService } from 'app/autism-gene-profiles-table/autism-gene-profiles-table.service';
import {
  AutismGeneProfileSingleViewComponent
} from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view.component';

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
    this.autismGeneProfilesService.getConfig().pipe(map(config => this.createTableConfig(config))).subscribe(config => {
      this.agpTableConfig = config;
      this.agpTableSortBy = this.findFirstAgpSortableCategory(config);
    });
    this.autismGeneProfilesService.getConfig().pipe(take(1)).subscribe(config => {
      this.agpSingleViewConfig = config;
    });
  }

  private createTableConfig(config: AgpSingleViewConfig): AgpTableConfig {
    const agpTableConfig = new AgpTableConfig();
    agpTableConfig.defaultDataset = config.defaultDataset;
    agpTableConfig.columns = [];
    agpTableConfig.pageSize = config.pageSize;

    const datasets = config.datasets;
    const geneSets = config.geneSets;
    const genomicScores = config.genomicScores;

    agpTableConfig.columns.push(
      new AgpColumn('createTab', [], 'Gene', false, 'geneSymbol', null, false, true)
    );

    geneSets.forEach(geneSet => {
      agpTableConfig.columns.push(this.createTableGeneSet(geneSet));
    });

    genomicScores.forEach(genomicScore => {
      agpTableConfig.columns.push(this.createTableGenomicScore(genomicScore));
    });

    datasets.forEach(dataset => {
      agpTableConfig.columns.push(this.createTableDataset(dataset));
    });

    const order = config.order.map(el => el.id);
    agpTableConfig.columns.sort((col1, col2) => order.indexOf(col1.id) - order.indexOf(col2.id));

    return agpTableConfig;
  }

  private createTableGeneSet(geneSet: AgpGeneSetsCategory): AgpColumn {
    const innerColumns: AgpColumn[] = [];
    geneSet.sets.forEach(set => {
      innerColumns.push(
        new AgpColumn(
          null,
          [],
          set.setId,
          true,
          `${geneSet.category}_rank.${set.setId}`,
          set.meta,
          true,
          set.defaultVisible
        )
      );
    });

    return new AgpColumn(
      null,
      innerColumns,
      geneSet.displayName,
      false,
      `${geneSet.category}_rank`,
      null,
      true,
      geneSet.defaultVisible
    );
  }

  private createTableGenomicScore(genomicScore: AgpGenomicScoresCategory): AgpColumn {
    const innerColumns: AgpColumn[] = [];
    genomicScore.scores.forEach(score => {
      innerColumns.push(
        new AgpColumn(
          null,
          [],
          score.scoreName,
          true,
          `${genomicScore.category}.${score.scoreName}`,
          score.meta,
          true,
          score.defaultVisible
        ));
    });

    return new AgpColumn(
      null,
      innerColumns,
      genomicScore.displayName,
      false,
      genomicScore.category,
      null,
      false,
      genomicScore.defaultVisible
    );
  }

  private createTableDataset(dataset: AgpDataset): AgpColumn {
    const personSetsColumns: AgpColumn[] = [];
    dataset.personSets.forEach(set => {
      const statisticsColumns: AgpColumn[] = [];
      set.statistics.forEach(statistic => {
        statisticsColumns.push(
          new AgpColumn(
            'goToQuery',
            [],
            statistic.displayName,
            false,
            `${dataset.id}.${set.id}.${statistic.id}`,
            null,
            true,
            statistic.defaultVisible
          )
        );
      });

      personSetsColumns.push(
        new AgpColumn(
          null,
          statisticsColumns,
          `${set.displayName} (${set.childrenCount})`,
          false,
          `${dataset.id}.${set.id}`,
          null,
          false,
          set.defaultVisible
        )
      );
    });

    return new AgpColumn(
      null, personSetsColumns, dataset.displayName, false, dataset.id, dataset.meta, false, dataset.defaultVisible
    );
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
    AutismGeneProfileSingleViewComponent.goToQuery(
      this.store, this.queryService, $event.geneSymbol, personSet, datasetId, statistic
    );
  }
}
