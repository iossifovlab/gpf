import { Component, OnInit } from '@angular/core';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { GeneProfilesService } from 'app/gene-profiles-block/gene-profiles.service';
import { GeneProfilesSingleViewConfig } from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { InstanceService } from 'app/instance.service';
import { environment } from 'environments/environment';
import { combineLatest, switchMap, take } from 'rxjs';

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

  public geneProfilesConfig: GeneProfilesSingleViewConfig;
  public homeDescription: string;

  public constructor(
    private instanceService: InstanceService,
    private datasetsService: DatasetsService,
    private datasetsTreeService: DatasetsTreeService,
    private geneProfilesService: GeneProfilesService,
  ) {}

  public ngOnInit(): void {
    combineLatest({
      datasets: this.datasetsTreeService.getDatasetHierarchy(),
      visibleDatasets: this.datasetsService.getVisibleDatasets()
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

    this.instanceService.getGpfVersion().subscribe(res => {
      this.gpfVersion = res;
    });

    this.geneProfilesService.getConfig().subscribe(res => {
      this.geneProfilesConfig = res;
    });

    this.instanceService.getHomeDescription().subscribe((res: {content: string}) => {
      this.homeDescription = res.content;
    });
  }

  public attachDatasetDescription(entry: object): void {
    entry['children']?.forEach((d: object) => this.attachDatasetDescription(d));
    this.datasetsService.getDatasetDescription(entry['dataset']).pipe(take(1)).subscribe(res => {
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
    this.instanceService.writeHomeDescription(markdown).pipe(
      take(1),
      switchMap(() => this.instanceService.getHomeDescription())
    ).subscribe((res: {content: string}) => {
      this.homeDescription = res.content;
    });
  }
}
