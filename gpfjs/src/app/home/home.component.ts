import { Component, OnInit } from '@angular/core';
import { AppVersionService } from 'app/app-version.service';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { AgpSingleViewConfig } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { environment } from 'environments/environment';
import { combineLatest, take } from 'rxjs';

@Component({
  selector: 'gpf-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  public gpfVersion = '';
  public gpfjsVersion = environment?.version;

  public allStudies = new Set();
  public visibleDatasets: string[];
  public datasets: string[] = [];
  public content: object = null;

  public loadingFinished = false;
  public studiesLoaded = 0;

  public agpConfig: AgpSingleViewConfig;

  public constructor(
    private appVersionService: AppVersionService,
    private datasetService: DatasetsService,
    private datasetsTreeService: DatasetsTreeService,
    private autismGeneProfilesService: AutismGeneProfilesService,

  ) {}

  public ngOnInit(): void {
    combineLatest({
      datasets: this.datasetsTreeService.getDatasetHierarchy(),
      visibleDatasets: this.datasetService.getVisibleDatasets()
    }).subscribe(({datasets, visibleDatasets}) => {
      datasets['data'].forEach((d: object) => {
        this.attachDatasetDescription(d); this.collectAllStudies(d);
      });

      this.content = datasets;
      this.visibleDatasets = visibleDatasets as string[];

      this.content['data'].forEach(d => {
        if (this.visibleDatasets.includes(d.dataset)) {
          this.datasets.push(d.dataset);
        }

        if (d.children) {
          d.children.map(c => c.dataset).forEach(c => {
            if (this.visibleDatasets.includes(c)) {
              this.datasets.push(c);
            }
          });
        }
      });
    });

    this.appVersionService.getGpfVersion().subscribe(res => {
      this.gpfVersion = res;
    });

    this.autismGeneProfilesService.getConfig().subscribe(res => {
      this.agpConfig = res;
    });
  }

  public attachDatasetDescription(entry: object): void {
    entry['children']?.forEach((d: object) => this.attachDatasetDescription(d));
    this.datasetService.getDatasetDescription(entry['dataset']).pipe(take(1)).subscribe(res => {
      if (res['description']) {
        entry['description'] = this.getFirstParagraph(res['description']);
      }

      this.studiesLoaded++;
      if (this.studiesLoaded === this.allStudies.size) {
        this.loadingFinished = true;
      }
    });
  }

  public getFirstParagraph(description: string): string {
    const splitDescription = description.split('\n\n');
    if (splitDescription[0].includes('#')) {
      const regexTitle = new RegExp(/^##((?:\n|.)*?)$\n/, 'm');
      const titleMatch = regexTitle.exec(splitDescription[0]);
      return titleMatch ? splitDescription[0].replace(/^##((?:\n|.)*?)$\n/m, '') : splitDescription[1];
    }
    return splitDescription[0];
  }

  public collectAllStudies(data: object): void {
    this.allStudies.add(data['dataset']);
    if (data['children'] && data['children'].length !== 0) {
      data['children'].forEach(dataset => {
        this.collectAllStudies(dataset);
      });
    }
  }

  public datasetHasVisibleChildren(children: string[]): boolean {
    let result = false;

    if (!children) {
      return result;
    }

    children.forEach(c => {
      if (this.visibleDatasets.includes(c['dataset'])) {
        result = true;
      }
    });
    return result;
  }

  public toggleDatasetCollapse(dataset): void {
    if (!this.visibleDatasets.includes(dataset.dataset)) {
      return;
    }

    const children = dataset.children.map(c => c.dataset);
    if (this.datasets.includes(dataset.children.map(d => d.dataset)[0])) {
      this.datasets = this.datasets.filter(a => !new Set(this.findAllByKey(dataset.children, 'dataset')).has(a));
    } else {
      children.forEach(c => {
        if (this.visibleDatasets.includes(c)) {
          this.datasets.push(c);
        }
      });
    }
  }

  public findAllByKey(obj, keyToFind): string[] {
    return Object.entries(obj)
      .reduce((acc, [key, value]) => (key === keyToFind)
        ? acc.concat(value)
        : (typeof value === 'object' && value)
        ? acc.concat(this.findAllByKey(value, keyToFind))
        : acc
      , [])
  }

  public writeDescription(markdown: string): void {
    // to do
  }
}
