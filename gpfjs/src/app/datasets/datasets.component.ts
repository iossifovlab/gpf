import { UsersService } from '../users/users.service';
import { Component, OnInit } from '@angular/core';
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
  selectedDataset: Dataset;
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

    this.datasets$ = this.filterHiddenGroups(this.datasetsService.getDatasetsObservable());

    this.createDatasetHierarchy();
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    this.setupSelectedDataset();

    this.datasetsService.getDatasetsLoadedObservable().subscribe(() => {
      this.setupSelectedDataset();
    });

    this.datasets$.pipe(take(1)).subscribe(datasets => {
      if (!this.datasetsService.hasLoadedAnyDataset && !this.datasetsService.hasSelectedDataset()) {
        this.datasetsService.setSelectedDataset(datasets[0]);
      }
    });

    this.usersService.getUserInfoObservable().subscribe(() => {
      this.datasetsService.reloadSelectedDataset(true);
    });

    this.datasetsService.getPermissionDeniedPrompt().subscribe(
      aprompt => this.permissionDeniedPrompt = aprompt
    );
  }

  setupSelectedDataset(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    if (!this.selectedDataset) {
      return;
    }

    this.registerAlertVisible = !this.selectedDataset.accessRights;

    if (!this.isToolSelected()) {
      this.router.navigate(['/', 'datasets', this.selectedDataset.id, this.findFirstTool(this.selectedDataset)]);
    } else {
      const url = this.router.url.split('/');
      const toolName = url[url.indexOf('datasets') + 2];

      if (!this.isToolEnabled(this.selectedDataset, toolName)) {
        this.router.navigate(['/', 'datasets', this.selectedDataset.id, this.findFirstTool(this.selectedDataset)]);
      }
    }
  }

  private isToolEnabled(dataset: Dataset, toolName: string): boolean {
    let result: boolean;

    switch (toolName) {
      case 'dataset-description':
        result = dataset.description !== undefined ? true : false;
        break;
      case 'dataset-statistics':
        result = dataset.commonReport['enabled'];
        break;
      case 'genotype-browser':
        result = (dataset.genotypeBrowser && dataset.genotypeBrowserConfig) !== undefined ? true : false;
        break;
      case 'phenotype-browser':
        result = dataset.phenotypeBrowser;
        break;
      case 'phenotype-tool':
        result = dataset.phenotypeTool;
        break;
      case 'enrichment-tool':
        result = dataset.enrichmentTool;
        break;
      case 'gene-browser':
        result = dataset.geneBrowser?.enabled;
        break;
    }

    return result;
  }

  isToolSelected(): boolean {
    return this.router.url.split('/').some(str => Object.values(toolPageLinks).includes(str));
  }

  findFirstTool(selectedDataset: Dataset): string {
    let firstTool = '';

    if (selectedDataset.description) {
      firstTool = toolPageLinks.datasetDescription;
    } else if (selectedDataset.commonReport['enabled']) {
      firstTool = toolPageLinks.datasetStatistics;
    } else if (selectedDataset.geneBrowser) {
      firstTool = toolPageLinks.geneBrowser;
    } else if (selectedDataset.genotypeBrowser && selectedDataset.genotypeBrowserConfig) {
      firstTool = toolPageLinks.genotypeBrowser;
    } else if (selectedDataset.phenotypeBrowser) {
      firstTool = toolPageLinks.phenotypeBrowser;
    } else if (selectedDataset.enrichmentTool) {
      firstTool = toolPageLinks.enrichmentTool;
    } else if (selectedDataset.phenotypeTool) {
      firstTool = toolPageLinks.phenotypeTool;
    }

    return firstTool;
  }

  createDatasetHierarchy(): void {
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

  routeChange(): void {
    /* In order to have state separation between the dataset tools,
    we clear the state if the previous url is from a different dataset tool */
    if (DatasetsComponent.previousUrl !== this.router.url && DatasetsComponent.previousUrl.startsWith('/datasets')) {
      this.store.dispatch(new StateResetAll());
    }
    DatasetsComponent.previousUrl = this.router.url;
  }
}
