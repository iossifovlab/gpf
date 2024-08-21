import { Component, OnInit, OnDestroy } from '@angular/core';
import { DatasetsService } from './datasets.service';
import { Dataset, toolPageLinks } from './datasets';
import { Subscription, combineLatest, of, switchMap, take } from 'rxjs';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { isEmpty } from 'lodash';
import { DatasetNode } from 'app/dataset-node/dataset-node';
import { Store } from '@ngxs/store';
import { Store as Store1 } from '@ngrx/store';
import { StateResetAll } from 'ngxs-reset-plugin';
import { GeneProfilesState } from 'app/gene-profiles-table/gene-profiles-table.state';
// import { DatasetNodeModel, DatasetNodeState, SetExpandedDatasets } from 'app/dataset-node/dataset-node.state';
import { selectDatasetId, setDatasetId } from './datasets.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';

@Component({
  selector: 'gpf-datasets',
  templateUrl: './datasets.component.html',
  styleUrls: ['./datasets.component.css'],
})
export class DatasetsComponent extends StatefulComponentNgRx implements OnInit, OnDestroy {
  private static previousUrl = '';
  public registerAlertVisible = false;
  public datasetTrees: DatasetNode[];
  public selectedDataset: Dataset = null;
  public permissionDeniedPrompt: string;
  public toolPageLinks = toolPageLinks;
  public visibleDatasets: string[];
  private subscriptions: Subscription[] = [];

  public selectedTool: string;

  public constructor(
    private datasetsService: DatasetsService,
    private route: ActivatedRoute,
    private router: Router,
    protected store1: Store1,
  ) {
    super(store1, 'dataset', selectDatasetId);
  }

  public ngOnInit(): void {
    this.datasetTrees = new Array<DatasetNode>();
    this.subscriptions.push(
      this.route.params.pipe(
        switchMap((params: Params) => {
          if (isEmpty(params)) {
            return of();
          }
          // Clear out previous loaded dataset - signifies loading and triggers change detection
          this.selectedDataset = null;
          return this.datasetsService.getDataset(params['dataset'] as string);
        })
      ).subscribe({
        next: dataset => {
          if (dataset) {
            this.store1.dispatch(setDatasetId({datasetId: dataset.id}));
            this.selectedDataset = dataset;
            this.setupSelectedDataset();
          }
        },
        error: () => {
          this.selectedDataset = undefined;
        }
      }),
      // Create dataset hierarchy
      combineLatest({
        datasets: this.datasetsService.getDatasetsObservable(),
        visibleDatasets: this.datasetsService.getVisibleDatasets()
      }).subscribe(({datasets, visibleDatasets}) => {
        this.visibleDatasets = visibleDatasets as string[];
        this.datasetTrees = new Array<DatasetNode>();
        datasets = datasets
          .filter(d => d.groups.find((g) => g.name === 'hidden') === undefined || d.accessRights)
          .filter(d => this.visibleDatasets.includes(d.id));
        datasets
          .sort((a, b) => this.visibleDatasets.indexOf(a.id) - this.visibleDatasets.indexOf(b.id))
          .filter(d => !d.parents.length)
          .map(d => this.datasetTrees.push(new DatasetNode(d, datasets)));

        this.saveTopLevelDatasetsToState();

        if (this.router.url === '/datasets' && this.datasetTrees.length > 0) {
          this.router.navigate(['/', 'datasets', this.datasetTrees[0].dataset.id]);
        }
      }),
      this.datasetsService.getPermissionDeniedPrompt().subscribe(aprompt => {
        this.permissionDeniedPrompt = aprompt;
      }),
    );
  }

  private saveTopLevelDatasetsToState(): void {
    // this.store.selectOnce(
    //   (state: { datasetNodeState: DatasetNodeModel}) => state.datasetNodeState)
    //   .subscribe(state => {
    //     this.datasetTrees.forEach(node => {
    //       state.expandedDatasets.push(node.dataset.id);
    //     });
    //     this.store.dispatch(new SetExpandedDatasets(state.expandedDatasets));
    //   });
  }

  public ngOnDestroy(): void {
    this.subscriptions.map(subscription => subscription.unsubscribe());
  }

  public get datasetsLoading(): boolean {
    return this.datasetsService.datasetsLoading;
  }

  private setupSelectedDataset(): void {
    const firstTool = this.findFirstTool(this.selectedDataset);
    this.selectedTool = firstTool;
    this.registerAlertVisible = !this.selectedDataset.accessRights;

    if (!this.isToolSelected()) {
      if (firstTool) {
        this.router.navigate(
          ['/', 'datasets', this.selectedDataset.id, firstTool],
          {replaceUrl: true}
        );
      } else {
        this.router.navigate(['/', 'datasets', this.selectedDataset.id]);
      }
    } else {
      const url = this.router.url.split('?')[0].split('/');
      const toolName = url[url.indexOf('datasets') + 2];

      if (!this.isToolEnabled(this.selectedDataset, toolName)) {
        this.router.navigate(['/', 'datasets', this.selectedDataset.id, firstTool]);
        this.selectedTool = firstTool;
      } else {
        this.selectedTool = toolName;
      }
    }
  }

  private isToolEnabled(dataset: Dataset, toolName: string): boolean {
    let result: boolean;
    switch (toolName) {
      case 'dataset-description':
        // Always true.
        result = true;
        break;
      case 'dataset-statistics':
        result = dataset.commonReport.enabled;
        break;
      case 'genotype-browser':
        result = Boolean(dataset.genotypeBrowser && (dataset.genotypeBrowserConfig !== undefined) !== false);
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
    return this.router.url.split('?')[0].split('/').some(str => Object.values(toolPageLinks).includes(str));
  }

  public findFirstTool(selectedDataset: Dataset): string {
    let firstTool = '';

    if (!selectedDataset.accessRights) {
      firstTool = toolPageLinks.datasetDescription;
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
    } else if (selectedDataset.commonReport.enabled) {
      firstTool = toolPageLinks.datasetStatistics;
    } else {
      firstTool = toolPageLinks.datasetDescription;
    }

    return firstTool;
  }

  public routeChange(): void {
    const url = this.router.url;

    /* In order to have state separation between the dataset tools,
    we clear the state if the previous url is from a different dataset tool */
    if (DatasetsComponent.previousUrl !== url && DatasetsComponent.previousUrl.startsWith('/datasets')) {
      // this.store.dispatch(new StateResetAll(GeneProfilesState, DatasetNodeState, DatasetState));
    }

    this.selectedTool = url.split('/').pop();
    DatasetsComponent.previousUrl = url;
  }
}
