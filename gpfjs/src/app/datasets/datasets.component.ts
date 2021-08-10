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
        this.selectedDataset$.pipe(take(1)).subscribe(dataset => {
          this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
        });
      } else {
        this.selectedDataset$.pipe(take(1)).subscribe(dataset => {
          const url = this.router.url.split('/');
          const toolName = url[url.indexOf('datasets') + 2];

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

  selectDataset(dataset: Dataset): void {
    if (dataset !== undefined) {
      this.router.navigate(['/', 'datasets', dataset.id, this.findFirstTool(dataset)]);
    }
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
