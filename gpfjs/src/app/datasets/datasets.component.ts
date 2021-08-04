import { UsersService } from '../users/users.service';
import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset, toolPageLinks } from './datasets';
// tslint:disable-next-line:import-blacklist
import { Observable } from 'rxjs';
import { ActivatedRoute, Params, Router } from '@angular/router';
import * as _ from 'lodash';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { Store } from '@ngxs/store';
import { StateResetAll } from 'ngxs-reset-plugin';
import { map, take } from 'rxjs/operators';

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
  public toolPageLinks = toolPageLinks;

  constructor(
    private usersService: UsersService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router,
    private store: Store,
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

    this.datasets$.pipe(take(1)).subscribe(datasets => {
      if (!this.datasetsService.hasSelectedDataset()) {
        this.selectDataset(datasets[0]);
      } else if (!this.isToolSelected()) {
        this.datasetsService.getSelectedDataset().pipe(take(1)).subscribe(dataset => {
          this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
        });
      } else {
        this.datasetsService.getSelectedDataset().pipe(take(1)).subscribe(dataset => {
          const url = this.router.url.split('/');
          const toolName = url[url.indexOf(dataset.id) + 1];

          if (!this.isToolEnabled(dataset, toolName)) {
            this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
          }
        });
      }
    });

    this.usersService.getUserInfoObservable().subscribe(() => {
      this.datasetsService.reloadSelectedDataset();
    });

    this.datasetsService.getPermissionDeniedPrompt().subscribe(
      aprompt => this.permissionDeniedPrompt = aprompt
    );
  }

  private isToolEnabled(dataset, toolName) {
    switch (toolName) {
      case 'dataset-description':
        return dataset.description;
      case 'dataset-statistics':
        return dataset.commonReport['enabled'];
      case 'genotype-browser':
        return dataset.genotypeBrowser && dataset.genotypeBrowserConfig;
      case 'phenotype-browser':
        return dataset.phenotypeBrowser;
      case 'phenotype-tool':
        return dataset.phenotypeTool;
      case 'enrichment-tool':
        return dataset.enrichmentTool;
      case 'gene-browser':
        return dataset.geneBrowser?.enabled;
    }
  }

  isToolSelected(): boolean {
    return this.router.url.split('/').some(str => Object.values(toolPageLinks).includes(str));
  }

  findFirstTool(selectedDataset: Dataset) {
    if (selectedDataset.description) {
      return toolPageLinks.datasetDescription;
    } else if (selectedDataset.commonReport['enabled']) {
      return toolPageLinks.datasetStatistics;
    } else if (selectedDataset.genotypeBrowser && selectedDataset.genotypeBrowserConfig) {
      return toolPageLinks.genotypeBrowser;
    } else if (selectedDataset.phenotypeBrowser) {
      return toolPageLinks.phenotypeBrowser;
    } else if (selectedDataset.enrichmentTool) {
      return toolPageLinks.enrichmentTool;
    } else if (selectedDataset.phenotypeTool) {
      return toolPageLinks.phenotypeTool;
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
    return datasets.pipe(map((d) =>
      d.filter(
        (dataset) =>
          dataset.groups.find((g) => g.name === 'hidden') == null ||
          dataset.accessRights
      )
    ));
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
      this.store.dispatch(new StateResetAll());
    }
    DatasetsComponent.previousUrl = this.router.url;
  }
}
