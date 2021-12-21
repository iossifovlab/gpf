import { UsersService } from '../users/users.service';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset, toolPageLinks } from './datasets';
// eslint-disable-next-line no-restricted-imports
import { Observable, Subscription } from 'rxjs';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { isEmpty } from 'lodash';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { Store } from '@ngxs/store';
import { StateResetAll } from 'ngxs-reset-plugin';
import { map, take } from 'rxjs/operators';

@Component({
  selector: 'gpf-datasets',
  templateUrl: './datasets.component.html',
  styleUrls: ['./datasets.component.css'],
})
export class DatasetsComponent implements OnInit, OnDestroy {
  private static previousUrl = '';
  public registerAlertVisible = false;
  private datasets$: Observable<Dataset[]>;
  public datasetTrees: DatasetNode[];
  public selectedDataset: Dataset;
  public permissionDeniedPrompt: string;
  public toolPageLinks = toolPageLinks;

  private subscriptions: Subscription[] = [];

  constructor(
    private usersService: UsersService,
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router,
    private store: Store,
  ) { }

  public ngOnInit() {
    this.datasetTrees = new Array<DatasetNode>();
    this.datasets$ = this.filterHiddenGroups(this.datasetsService.getDatasetsObservable());
    this.subscriptions.push(
      this.route.params.subscribe((params: Params) => {
        if (isEmpty(params)) {
          return;
        }
        // Clear out previous loaded dataset - signifies loading and triggers change detection
        this.selectedDataset = null;
        this.datasetsService.setSelectedDatasetById(params['dataset']);
      }),
      // Create dataset hierarchy
      this.datasets$.subscribe(datasets => {
        this.datasetTrees = new Array<DatasetNode>();
        datasets.filter(d => !d.parents.length).map(d => this.datasetTrees.push(new DatasetNode(d, datasets)));
      }),
      this.datasetsService.getDatasetsLoadedObservable().subscribe((res) => {
        this.setupSelectedDataset();
      }),
      this.datasets$.pipe(take(1)).subscribe(datasets => {
        if (this.router.url === '/datasets') {
          this.router.navigate(['/', 'datasets', datasets[0].id]);
        }
      }),
      this.usersService.getUserInfoObservable().subscribe(() => {
        this.datasetsService.reloadSelectedDataset(true);
      }),
      this.datasetsService.getPermissionDeniedPrompt().subscribe(
        aprompt => this.permissionDeniedPrompt = aprompt
      ),
    );
  }

  public ngOnDestroy() {
    this.subscriptions.map(subscription => subscription.unsubscribe());
  }

  public get datasetsLoading(): boolean {
    return this.datasetsService.datasetsLoading;
  }

  private setupSelectedDataset(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    if (!this.selectedDataset) {
      return;
    }

    this.registerAlertVisible = !this.selectedDataset.accessRights;

    if (!this.isToolSelected()) {
      const firstTool = this.findFirstTool(this.selectedDataset);
      if (firstTool) {
        this.router.navigate(['/', 'datasets', this.selectedDataset.id, this.findFirstTool(this.selectedDataset)]);
      } else {
        this.router.navigate(['/', 'datasets', this.selectedDataset.id]);
      }
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
        result = dataset.commonReport.enabled;
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
        result = dataset.geneBrowser.enabled;
        break;
    }

    return result;
  }

  private isToolSelected(): boolean {
    return this.router.url.split('/').some(str => Object.values(toolPageLinks).includes(str));
  }

  public findFirstTool(selectedDataset: Dataset): string {
    let firstTool = '';

    if (selectedDataset.description) {
      firstTool = toolPageLinks.datasetDescription;
    } else if (selectedDataset.commonReport.enabled) {
      firstTool = toolPageLinks.datasetStatistics;
    } else if (selectedDataset.geneBrowser.enabled) {
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

  private filterHiddenGroups(datasets: Observable<Dataset[]>): Observable<Dataset[]> {
    return datasets.pipe(map((d) =>
      d.filter((dataset) => dataset.groups.find((g) => g.name === 'hidden') == null || dataset.accessRights)
    ));
  }

  public routeChange(): void {
    /* In order to have state separation between the dataset tools,
    we clear the state if the previous url is from a different dataset tool */
    if (DatasetsComponent.previousUrl !== this.router.url && DatasetsComponent.previousUrl.startsWith('/datasets')) {
      this.store.dispatch(new StateResetAll());
    }
    DatasetsComponent.previousUrl = this.router.url;
  }
}
