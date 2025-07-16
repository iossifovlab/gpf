import { APP_BASE_HREF } from '@angular/common';
import { Component, ElementRef, Inject, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { DatasetHierarchy } from 'app/datasets/datasets';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { DatasetsService } from 'app/datasets/datasets.service';
import { Gene } from 'app/gene-browser/gene';
import { GeneService } from 'app/gene-browser/gene.service';
import { GeneProfilesService } from 'app/gene-profiles-block/gene-profiles.service';
import { GeneProfilesSingleViewConfig } from 'app/gene-profiles-single-view/gene-profiles-single-view';
import { GeneProfilesTableService } from 'app/gene-profiles-table/gene-profiles-table.service';
import { InstanceService } from 'app/instance.service';
import { environment } from 'environments/environment';
import { Subject, Subscription, combineLatest, debounceTime, distinctUntilChanged, of, switchMap, take } from 'rxjs';

@Component({
    selector: 'gpf-home',
    templateUrl: './home.component.html',
    styleUrls: ['./home.component.css'],
    standalone: false
})
export class HomeComponent implements OnInit, OnDestroy {
  private subscription: Subscription = new Subscription();

  public gpfVersion = '';
  public gpfjsVersion = environment?.version;

  public allStudies = new Set();
  public visibleDatasets: string[];
  public datasets: string[] = [];
  public content: DatasetHierarchy[] = null;
  public loadingFinished = false;
  public studiesLoaded = 0;
  public geneProfilesConfig: GeneProfilesSingleViewConfig;
  public homeDescription: string;

  @ViewChild('searchBox') private searchBox: ElementRef;
  @ViewChild('trigger') private dropdownTrigger: MatAutocompleteTrigger;
  public selectedGene: Gene;
  public geneSymbol = '';
  public geneSymbolSuggestions: string[] = [];
  public searchBoxInput$: Subject<string> = new Subject();
  private keystrokeSubscription: Subscription;
  public showError = false;

  public constructor(
    private instanceService: InstanceService,
    private datasetsService: DatasetsService,
    private datasetsTreeService: DatasetsTreeService,
    private geneProfilesService: GeneProfilesService,
    private geneProfilesTableService: GeneProfilesTableService,
    private geneService: GeneService,
    @Inject(APP_BASE_HREF) private baseHref: string,
  ) {}

  public ngOnInit(): void {
    this.subscription.add(combineLatest({
      datasets: this.datasetsTreeService.getDatasetHierarchy(),
      visibleDatasets: this.datasetsService.getVisibleDatasets()
    }).subscribe(({datasets, visibleDatasets}) => {
      datasets.forEach((d: DatasetHierarchy) => {
        this.collectAllStudies(d);
        this.attachDatasetDescription(d);
      });

      this.content = datasets;
      this.visibleDatasets = visibleDatasets;

      this.content.forEach(d => {
        if (this.visibleDatasets.includes(d.id)) {
          this.datasets.push(d.id);
        }

        if (d.children) {
          d.children.map(c => c.id).forEach(c => {
            if (this.visibleDatasets.includes(c)) {
              this.datasets.push(c);
            }
          });
        }
      });
    }));

    this.subscription.add(this.instanceService.getGpfVersion().subscribe(res => {
      this.gpfVersion = res;
    }));

    this.subscription.add(this.geneProfilesService.getConfig().subscribe(res => {
      this.geneProfilesConfig = res;
    }));

    this.subscription.add(this.instanceService.getHomeDescription().subscribe((res: {content: string}) => {
      this.homeDescription = res.content;
    }));

    this.subscription.add(this.searchBoxInput$.pipe(
      distinctUntilChanged(),
      debounceTime(250),
      switchMap(searchTerm => {
        if (!searchTerm) {
          return of(null);
        }
        return this.geneProfilesTableService.getGeneSymbols(1, searchTerm);
      })
    ).subscribe((response: string[]) => {
      if (!response) {
        this.geneSymbolSuggestions = [];
        return;
      }
      this.geneSymbolSuggestions = response;
    }));
  }

  public openSingleView(searchTerm: string): void {
    (this.searchBox.nativeElement as HTMLElement).blur();
    if (this.showError) {
      return;
    }

    if (searchTerm) {
      this.geneSymbol = searchTerm.trim();
    }

    if (!this.geneSymbol) {
      return;
    }

    this.subscription.add(this.geneService.getGene(this.geneSymbol.trim())
      .subscribe({
        next: gene => {
          this.geneSymbol = gene.geneSymbol;
          const geneProfilesBaseUrl = `${window.location.origin}${this.baseHref}/gene-profiles`;
          window.location.assign(`${geneProfilesBaseUrl}/${this.geneSymbol}`);
        },
        error: error => {
          console.error(error);
          this.showError = true;
          this.dropdownTrigger.closePanel();
        }
      }));
  }

  public reset(): void {
    this.geneSymbol = '';
    this.showError = false;
    this.geneSymbolSuggestions = [];
  }

  public attachDatasetDescription(entry: DatasetHierarchy): void {
    entry.children?.forEach((d: DatasetHierarchy) => this.attachDatasetDescription(d));
    this.subscription.add(this.datasetsService.getDatasetDescription(entry.id).subscribe(desc => {
      if (desc) {
        entry.description = this.getFirstParagraph(desc);
      }

      this.studiesLoaded++;
      if (this.studiesLoaded === this.allStudies.size) {
        this.loadingFinished = true;
      }
    }));
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

  public collectAllStudies(data: DatasetHierarchy): void {
    this.allStudies.add(data.id);
    if (data.children && data.children.length !== 0) {
      data.children.forEach(dataset => {
        this.collectAllStudies(dataset);
      });
    }
  }

  public datasetHasVisibleChildren(children: DatasetHierarchy[]): boolean {
    let result = false;

    if (!children) {
      return result;
    }

    children.forEach(c => {
      if (this.visibleDatasets.includes(c.id)) {
        result = true;
      }
    });
    return result;
  }

  public toggleDatasetCollapse(dataset: DatasetHierarchy): void {
    if (!this.visibleDatasets.includes(dataset.id)) {
      return;
    }

    const children = dataset.children.map(c => c.id);
    if (this.datasets.includes(children[0])) {
      this.datasets = this.datasets.filter(a => !new Set(this.findAllByKey(dataset.children, 'id')).has(a));
    } else {
      children.forEach(c => {
        if (this.visibleDatasets.includes(c)) {
          this.datasets.push(c);
        }
      });
    }
  }

  public findAllByKey(obj, keyToFind: string): string[] {
    return Object.entries(obj)
      .reduce((acc, [key, value]) => key === keyToFind
        ? acc.concat(value)
        : typeof value === 'object' && value
          ? acc.concat(this.findAllByKey(value, keyToFind))
          : acc
      , []);
  }

  public writeDescription(markdown: string): void {
    this.subscription.add(this.instanceService.writeHomeDescription(markdown).pipe(
      take(1),
      switchMap(() => this.instanceService.getHomeDescription())
    ).subscribe((res: {content: string}) => {
      this.homeDescription = res.content;
    }));
  }

  public ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
