import { Component, OnInit } from '@angular/core';
import {
  GeneProfilesDataset,
  GeneProfilesGeneSetsCategory,
  GeneProfilesGeneScoresCategory,
  GeneProfilesSingleViewConfig} from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { GeneProfilesService } from 'app/gene-profiles-block/gene-profiles.service';
import { map, take } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import { QueryService } from 'app/query/query.service';
import { GeneProfilesColumn, GeneProfilesTableConfig } from 'app/gene-profiles-table/gene-profiles-table';
import {
  GeneProfileSingleViewComponent
} from 'app/gene-profiles-single-view/gene-profiles-single-view.component';
import { cloneDeep } from 'lodash';

@Component({
  selector: 'gpf-gene-profiles-block',
  templateUrl: './gene-profiles-block.component.html',
  standalone: false
})
export class GeneProfilesBlockComponent implements OnInit {
  public geneProfilesTableConfig: GeneProfilesTableConfig;
  public geneProfilesSingleViewConfig: GeneProfilesSingleViewConfig;
  private geneProfilesTableConfigOriginal: GeneProfilesTableConfig;

  public constructor(
    private geneProfilesService: GeneProfilesService,
    private queryService: QueryService,
    private store: Store,
  ) { }

  public ngOnInit(): void {
    this.getConfig();

    this.geneProfilesService.getConfig().pipe(take(1)).subscribe(config => {
      this.geneProfilesSingleViewConfig = config;
    });
  }

  public getConfig(): void {
    this.geneProfilesService.getConfig().pipe(
      map(config => this.createTableConfig(config)
      )
    ).subscribe((config: GeneProfilesTableConfig) => {
      this.geneProfilesTableConfig = config;
      this.geneProfilesTableConfigOriginal = cloneDeep(config);
    });
  }

  public resetConf(): void {
    this.geneProfilesTableConfig = cloneDeep(this.geneProfilesTableConfigOriginal);
  }

  private createTableConfig(config: GeneProfilesSingleViewConfig): GeneProfilesTableConfig {
    const geneProfilesTableConfig = new GeneProfilesTableConfig();
    geneProfilesTableConfig.defaultDataset = config.defaultDataset;
    geneProfilesTableConfig.columns = [];
    geneProfilesTableConfig.pageSize = config.pageSize;

    const datasets = config.datasets;
    const geneSets = config.geneSets;
    const geneScores = config.geneScores;

    geneProfilesTableConfig.columns.push(
      new GeneProfilesColumn('createTab', [], 'Gene', false, 'geneSymbol', null, false, true, null)
    );

    geneSets.forEach(geneSet => {
      geneProfilesTableConfig.columns.push(this.createTableGeneSet(geneSet));
    });

    geneScores.forEach(geneScore => {
      geneProfilesTableConfig.columns.push(this.createTableGeneScore(geneScore));
    });

    datasets.forEach(dataset => {
      geneProfilesTableConfig.columns.push(this.createTableDataset(dataset));
    });

    const order = config.order.map(el => el.id);
    geneProfilesTableConfig.columns.sort((col1, col2) => order.indexOf(col1.id) - order.indexOf(col2.id));

    return geneProfilesTableConfig;
  }

  private createTableGeneSet(geneSet: GeneProfilesGeneSetsCategory): GeneProfilesColumn {
    const innerColumns: GeneProfilesColumn[] = [];
    geneSet.sets.forEach(set => {
      innerColumns.push(
        new GeneProfilesColumn(
          null,
          [],
          set.setId,
          true,
          `${geneSet.category}_rank.${set.setId}`,
          set.meta,
          true,
          set.defaultVisible,
          null
        )
      );
    });

    return new GeneProfilesColumn(
      null,
      innerColumns,
      geneSet.displayName,
      false,
      `${geneSet.category}_rank`,
      null,
      true,
      geneSet.defaultVisible,
      null
    );
  }

  private createTableGeneScore(geneScore: GeneProfilesGeneScoresCategory): GeneProfilesColumn {
    const innerColumns: GeneProfilesColumn[] = [];
    geneScore.scores.forEach(score => {
      innerColumns.push(
        new GeneProfilesColumn(
          null,
          [],
          score.scoreName,
          true,
          `${geneScore.category}.${score.scoreName}`,
          score.meta,
          true,
          score.defaultVisible,
          score.format
        ));
    });

    return new GeneProfilesColumn(
      null,
      innerColumns,
      geneScore.displayName,
      false,
      geneScore.category,
      null,
      false,
      geneScore.defaultVisible,
      null
    );
  }

  private createTableDataset(dataset: GeneProfilesDataset): GeneProfilesColumn {
    const personSetsColumns: GeneProfilesColumn[] = [];
    dataset.personSets.forEach(set => {
      const statisticsColumns: GeneProfilesColumn[] = [];
      set.statistics.forEach(statistic => {
        statisticsColumns.push(
          new GeneProfilesColumn(
            'goToQuery',
            [],
            statistic.displayName,
            false,
            `${dataset.id}.${set.id}.${statistic.id}`,
            null,
            true,
            statistic.defaultVisible,
            null
          )
        );
      });

      personSetsColumns.push(
        new GeneProfilesColumn(
          null,
          statisticsColumns,
          `${set.displayName} (${set.childrenCount})`,
          false,
          `${dataset.id}.${set.id}`,
          null,
          false,
          set.defaultVisible,
          null
        )
      );
    });

    return new GeneProfilesColumn(
      null, personSetsColumns, dataset.displayName, false, dataset.id, dataset.meta, false, dataset.defaultVisible, null
    );
  }

  public goToQueryEventHandler($event: { geneSymbol: string; statisticId: string; newTab: boolean }): void {
    const tokens: string[] = $event.statisticId.split('.');
    const datasetId = tokens[0];
    const personSet = this.geneProfilesSingleViewConfig.datasets
      .find(ds => ds.id === datasetId).personSets
      .find(ps => ps.id === tokens[1]);
    const statistic = personSet.statistics.find(st => st.id === tokens[2]);
    GeneProfileSingleViewComponent.goToQuery(
      this.store,
      this.queryService,
      $event.geneSymbol,
      personSet,
      datasetId,
      statistic,
      $event.newTab
    );
  }
}
