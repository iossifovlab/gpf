import { UsersService } from '../users/users.service';
import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset } from './datasets';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { Location } from '@angular/common';
import * as _ from 'lodash';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { StateRestoreService } from 'app/store/state-restore.service';

@Component({
  selector: 'gpf-datasets',
  templateUrl: './datasets.component.html',
  styleUrls: ['./datasets.component.css'],
})
export class DatasetsComponent implements OnInit {
  static previousUrl = '';
  registerAlertVisible = false;
  datasets$: Observable<Dataset[]>;
  datasetTrees: DatasetNode[];
  selectedDataset$: Observable<Dataset>;
  permissionDeniedPrompt: string;

  constructor(
    private usersService: UsersService,
    private stateRestoreService: StateRestoreService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router,
  ) { }

  ngOnInit() {
    this.route.params.subscribe(
      (params: Params) => {
        this.datasetsService.setSelectedDatasetById(params['dataset']);
      });

    this.datasets$ = this.filterHiddenGroups(
      this.datasetsService.getDatasetsObservable());

    this.createDatasetHierarchy();
    this.selectedDataset$ = this.datasetsService.getSelectedDataset();

    this.selectedDataset$
    .subscribe(selectedDataset => {
      if (!selectedDataset) {
        return;
      }
      this.registerAlertVisible = !selectedDataset.accessRights;
    });

    this.datasets$
      .take(1)
      .subscribe(datasets => {
        if (!this.datasetsService.hasSelectedDataset()) {
          this.selectDataset(datasets[0]);
        } else {
          if (!this.isToolSelected()) {
            this.datasetsService.getSelectedDataset().take(1).subscribe(dataset => {
              this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
            });
          }
        }
      });

    this.usersService.getUserInfoObservable()
      .subscribe(() => {
        this.datasetsService.reloadSelectedDataset();
      });

    this.datasetsService.getPermissionDeniedPrompt().subscribe(
      aprompt => this.permissionDeniedPrompt = aprompt
    );
  }


  isToolSelected(): boolean {
    const tools = ['dataset-description', 'dataset-statistics', 'genotype-browser', 'phenotype-browser', 'enrichment-tool', 'phenotype-tool'];
    return this.router.url.split('/').some(str => tools.includes(str));
  }

  findFirstTool(selectedDataset: Dataset) {
    if (selectedDataset.description) {
      return 'dataset-description';
    } else if (selectedDataset.commonReport['enabled']) {
      return 'dataset-statistics';
    } else if (selectedDataset.genotypeBrowser && selectedDataset.genotypeBrowserConfig) {
      return 'genotype-browser';
    } else if (selectedDataset.phenotypeBrowser) {
      return 'phenotype-browser';
    } else if (selectedDataset.enrichmentTool) {
      return 'enrichment-tool';
    } else if (selectedDataset.phenotypeTool) {
      return 'phenotype-tool';
    } else {
      return '';
    }
  }

  createDatasetHierarchy() {
    this.datasets$.subscribe((datasets) => {
      this.datasetTrees = new Array<DatasetNode>();
      datasets.forEach(d => {
        if (!d.parents.length) {
          this.datasetTrees.push(new DatasetNode(d, datasets));
        }
      });
    });
  }

  filterHiddenGroups(datasets: Observable<Dataset[]>): Observable<Dataset[]> {
    return datasets.map((d) =>
      d.filter(
        (dataset) =>
          dataset.groups.find((g) => g.name === 'hidden') == null ||
          dataset.accessRights
      )
    );
  }

  selectDataset(dataset: Dataset) {
    if (dataset !== undefined) {
      this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
    }
  }

  routeChange() {
    /* In order to have state separation between the dataset tools,
    we clear the state if the previous url is from a different dataset tool */
    if (DatasetsComponent.previousUrl !== this.router.url && DatasetsComponent.previousUrl.startsWith('/datasets')) {
      this.stateRestoreService.pushNewState({});
    }
    DatasetsComponent.previousUrl = this.router.url;
  }
}
