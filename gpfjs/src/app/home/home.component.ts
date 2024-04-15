import { APP_BASE_HREF } from '@angular/common';
import { Component, ElementRef, Inject, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { NgbDropdown } from '@ng-bootstrap/ng-bootstrap';
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
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {
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

  @ViewChild(NgbDropdown) private dropdown: NgbDropdown;
  @ViewChild('searchBox') private searchBox: ElementRef;
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
    combineLatest({
      datasets: this.datasetsTreeService.getDatasetHierarchy(),
      visibleDatasets: this.datasetsService.getVisibleDatasets()
    }).subscribe(({datasets, visibleDatasets}) => {
      (datasets['data'] as Array<object>).forEach((d: object) => {
        this.collectAllStudies(d); this.attachDatasetDescription(d);
      });

      this.content = datasets;
      this.visibleDatasets = visibleDatasets as string[];

      (this.content['data'] as Array<object>).forEach(d => {
        if (this.visibleDatasets.includes(d['dataset'] as string)) {
          this.datasets.push(d['dataset'] as string);
        }

        if (d['children'] as Array<object>) {
          (d['children'] as Array<object>).map(c => c['dataset'] as string).forEach(c => {
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

    this.keystrokeSubscription = this.searchBoxInput$.pipe(
      distinctUntilChanged(),
      debounceTime(250),
      switchMap(searchTerm => {
        if (!searchTerm) {
          return of(null);
        }
        return this.geneProfilesTableService.getGenes(1, searchTerm);
      })
    ).subscribe((response: {geneSymbol: string}[]) => {
      if (!response) {
        this.geneSymbolSuggestions = [];
        return;
      }
      this.geneSymbolSuggestions = response.map(gene => gene.geneSymbol);
    });
  }

  public ngOnDestroy(): void {
    this.keystrokeSubscription.unsubscribe();
  }

  public openSingleView(searchTerm: string): void {
    if (this.showError) {
      return;
    }

    if (searchTerm) {
      this.geneSymbol = searchTerm.trim();
    }

    if (!this.geneSymbol) {
      return;
    }

    this.closeDropdown();

    this.geneService.getGene(this.geneSymbol.trim())
      .subscribe({
        next: gene => {
          this.geneSymbol = gene.geneSymbol;
          const geneProfilesBaseUrl = `${window.location.origin}${this.baseHref}/gene-profiles`;
          window.location.assign(`${geneProfilesBaseUrl}/${this.geneSymbol}`);
        },
        error: error => {
          console.error(error);
          this.showError = true;
        }
      });
  }

  public openDropdown(): void {
    if (this.dropdown && !this.dropdown.isOpen()) {
      this.dropdown.open();
    }
  }

  public closeDropdown(): void {
    if (this.dropdown && this.dropdown.isOpen()) {
      this.dropdown.close();
      (this.searchBox.nativeElement as HTMLElement).blur();
    }
  }

  public attachDatasetDescription(entry: object): void {
    entry['children']?.forEach((d: object) => this.attachDatasetDescription(d));
    this.datasetsService.getDatasetDescription(entry['dataset'] as string).subscribe(res => {
      if (res['description']) {
        entry['description'] = this.getFirstParagraph(res['description'] as string);
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
    if (data['children'] && (data['children'] as Array<object>).length !== 0) {
      (data['children'] as Array<object>).forEach(dataset => {
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
      if (this.visibleDatasets.includes(c['dataset'] as string)) {
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
    this.instanceService.writeHomeDescription(markdown).pipe(
      take(1),
      switchMap(() => this.instanceService.getHomeDescription())
    ).subscribe((res: {content: string}) => {
      this.homeDescription = res.content;
    });
  }
}
