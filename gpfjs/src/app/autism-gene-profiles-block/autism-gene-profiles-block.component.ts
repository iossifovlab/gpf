import { Component, OnInit } from '@angular/core';
import { AgpSingleViewConfig } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
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
    agpTableConfig.pageSize = 20; // ???????

    const geneColumn = new AgpColumn();
    geneColumn.clickable = 'createTab';
    geneColumn.columns = [];
    geneColumn.displayName = 'Gene';
    geneColumn.displayVertical = false;
    geneColumn.id = 'geneSymbol';
    geneColumn.meta = null;
    geneColumn.sortable = false;
    geneColumn.visibility = true;
    agpTableConfig.columns.push(geneColumn);

    const datasets = config.datasets;
    const geneSets = config.geneSets;
    const genomicScores = config.genomicScores;

    geneSets.forEach(geneSet => {
      const setColumn = new AgpColumn();
      setColumn.clickable = null;
      setColumn.columns = [];
      setColumn.displayName = geneSet.displayName;
      setColumn.displayVertical = false;
      setColumn.id = geneSet.category + '_rank';
      setColumn.meta = null;
      setColumn.sortable = true;

      geneSet.sets.forEach(set => {
        const column = new AgpColumn();
        column.clickable = null;
        column.columns = [];
        column.displayName = set.setId;
        column.displayVertical = true;
        column.id = setColumn.id + '.' + set.setId;
        column.meta = null;
        column.sortable = true;
        column.visibility = set.defaultVisible;

        setColumn.columns.push(column);
      });

      setColumn.visibility = geneSet.defaultVisible;
      agpTableConfig.columns.push(setColumn);
    });

    genomicScores.forEach(genomicScore => {
      const scoreColumn = new AgpColumn();
      scoreColumn.clickable = null;
      scoreColumn.columns = [];
      scoreColumn.displayName = genomicScore.displayName;
      scoreColumn.displayVertical = false;
      scoreColumn.id = genomicScore.category;
      scoreColumn.meta = null;
      scoreColumn.sortable = false;

      genomicScore.scores.forEach(score => {
        const column = new AgpColumn();
        column.clickable = null;
        column.columns = [];
        column.displayName = score.scoreName;
        column.displayVertical = true;
        column.id = scoreColumn.id + '.' + score.scoreName;
        column.meta = null;
        column.sortable = true;
        column.visibility = score.defaultVisible;

        scoreColumn.columns.push(column);
      });

      scoreColumn.visibility = genomicScore.defaultVisible;
      agpTableConfig.columns.push(scoreColumn);
    });

    datasets.forEach(dataset => {
      const datasetColumn = new AgpColumn();
      datasetColumn.clickable = null;
      datasetColumn.columns = [];
      datasetColumn.displayName = dataset.displayName;
      datasetColumn.displayVertical = false;
      datasetColumn.id = dataset.id;
      datasetColumn.meta = null;
      datasetColumn.sortable = false;

      dataset.personSets.forEach(set => {
        const column = new AgpColumn();
        column.clickable = null;
        column.columns = [];
        column.displayName = `${set.displayName} (${set.childrenCount})`;
        column.displayVertical = false;
        column.id = dataset.id + '.' + set.id;
        column.meta = null;
        column.sortable = false;

        set.statistics.forEach(statistic => {
          const statisticsColumn = new AgpColumn();
          statisticsColumn.clickable = 'goToQuery';
          statisticsColumn.columns = [];
          statisticsColumn.displayName = statistic.displayName;
          statisticsColumn.displayVertical = false;
          statisticsColumn.id = column.id + '.' + statistic.id;
          statisticsColumn.meta = null;
          statisticsColumn.sortable = true;
          statisticsColumn.visibility = statistic.defaultVisible;

          column.columns.push(statisticsColumn);
        });

        column.visibility = set.defaultVisible;
        datasetColumn.columns.push(column);
      });

      datasetColumn.visibility = dataset.defaultVisible;
      agpTableConfig.columns.push(datasetColumn);
    });

    const order = config.order.map(el => el.id);
    agpTableConfig.columns.sort((col1, col2) => order.indexOf(col1.id) - order.indexOf(col2.id));

    return agpTableConfig;
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
