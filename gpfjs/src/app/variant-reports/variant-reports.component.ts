import { Component, OnInit, HostListener, Pipe, PipeTransform, ViewChild, ElementRef } from '@angular/core';
import { VariantReportsService } from './variant-reports.service';
import {
  VariantReport, FamilyCounter, PedigreeCounter, EffectTypeTable, DeNovoData, PedigreeTable, PeopleCounter
} from './variant-reports';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { Dictionary } from 'lodash';
import * as _ from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ConfigService } from 'app/config/config.service';

@Pipe({ name: 'getPeopleCounterRow' })
export class PeopleCounterRowPipe implements PipeTransform {
  public transform(currentPeopleCounterRow: string): string {
    const result = currentPeopleCounterRow.replace('people_', '');
    return result[0].toUpperCase() + result.substring(1);
  }
}

@Component({
  selector: 'gpf-variant-reports',
  templateUrl: './variant-reports.component.html',
  styleUrls: ['./variant-reports.component.css']
})
export class VariantReportsComponent implements OnInit {
  public tags: Array<string> = new Array<string>();

  public currentPeopleCounter: PeopleCounter;
  public currentPedigreeTable: PedigreeTable;
  public currentDenovoReport: EffectTypeTable;
  public tagsHeader = '';
  public familiesCount = 0;
  public isAddClicked = false;
  public isRemoveClicked = false;

  public modal: NgbModalRef;
  @ViewChild('tagsModal') public tagsModal: ElementRef;

  public tagsModalsNumberOfRows = 9;
  public tagsModalsNumberOfCols = 2;

  public variantReport: VariantReport;
  public familiesCounters: FamilyCounter[];
  public pedigreeTables: PedigreeTable[];

  public selectedDataset: Dataset;

  public imgPathPrefix = environment.imgPathPrefix;
  public orderedTagList = [];
  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public filtersButtonsState: Record<string, number> = {};
  public tagIntersection = true; // mode "And"

  public denovoVariantsTableWidth: number;
  private denovoVariantsTableColumnWidth = 140;

  public constructor(
    public modalService: NgbModal,
    public config: ConfigService,
    private variantReportsService: VariantReportsService,
    private datasetsService: DatasetsService
  ) { }

  @HostListener('window:resize')
  public onResize(): void {
    this.calculateDenovoVariantsTableWidth();
  }

  public ngOnInit(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    this.variantReportsService.getVariantReport(this.selectedDataset.id).pipe(take(1)).subscribe(params => {
      this.variantReport = params;
      this.familiesCounters = this.variantReport.familyReport.familiesCounters;
      this.pedigreeTables = this.familiesCounters.map(
        familiesCounters => new PedigreeTable(
          this.chunkPedigrees(familiesCounters.pedigreeCounters),
          familiesCounters.phenotypes, familiesCounters.groupName,
          familiesCounters.legend
        )
      );
      this.currentPeopleCounter = this.variantReport.peopleReport.peopleCounters[0];
      this.currentPedigreeTable = this.pedigreeTables[0];
      if (this.variantReport.denovoReport !== null) {
        this.currentDenovoReport = this.variantReport.denovoReport.tables[0];
        this.calculateDenovoVariantsTableWidth();
      }
      this.updateFamiliesCount();
    });
    if (this.variantReportsService.getTags() !== undefined) {
      this.variantReportsService.getTags().subscribe(data => {
        Object.values(data).forEach((tag: string) => {
          this.tags.push(tag);
          this.orderedTagList.push(tag);
          this.filtersButtonsState[tag] = 0;
        });
        // Calculate square looking grid for the tags (1 column width === ~5 tags height)
        this.tagsModalsNumberOfCols = Math.ceil(Math.sqrt(Math.ceil(this.tags.length / 5)));
        this.tagsModalsNumberOfRows = Math.ceil(this.tags.length / this.tagsModalsNumberOfCols);
      });
    }
  }

  private copyOriginalPedigreeCounters(): Record<string, PedigreeCounter[]> {
    return this.familiesCounters.reduce(
      (obj, x) => {
        obj[x.groupName] = Array.from(x.pedigreeCounters); return obj;
      }, {}
    );
  }

  public addFilter(tag: string): void {
    if (this.filtersButtonsState[tag] === 1) {
      this.filtersButtonsState[tag] = 0;
    } else {
      this.filtersButtonsState[tag] = 1;
    }
    this.updateSelectedTagsList(tag);
    this.updateTagFilters();
    this.updateFamiliesCount();
  }

  public removeFilter(tag: string): void {
    if (this.filtersButtonsState[tag] === -1) {
      this.filtersButtonsState[tag] = 0;
    } else {
      this.filtersButtonsState[tag] = -1;
    }
    this.updateDeselectedTagsList(tag);
    this.updateTagFilters();
    this.updateFamiliesCount();
  }

  public updateSelectedTagsList(tag: string): void {
    if (!this.selectedTags.includes(tag)) {
      this.selectedTags.push(tag);
    } else {
      const index = this.selectedTags.indexOf(tag);
      this.selectedTags.splice(index, 1);
    }
    if (this.deselectedTags.includes(tag)) {
      const index = this.deselectedTags.indexOf(tag);
      this.deselectedTags.splice(index, 1);
    }
    this.updateTagsHeader();
  }

  public updateDeselectedTagsList(tag: string): void {
    if (!this.deselectedTags.includes(tag)) {
      this.deselectedTags.push(tag);
    } else {
      const index = this.deselectedTags.indexOf(tag);
      this.deselectedTags.splice(index, 1);
    }
    if (this.selectedTags.includes(tag)) {
      const index = this.selectedTags.indexOf(tag);
      this.selectedTags.splice(index, 1);
    }
    this.updateTagsHeader();
  }

  public updateTagsHeader(): void {
    this.tagsHeader = '';
    if (this.selectedTags.length > 0) {
      this.tagsHeader += this.selectedTags.join(', ');
    }

    if (this.deselectedTags.length > 0 && this.selectedTags.length > 0) {
      this.tagsHeader += ', ';
      this.tagsHeader += this.deselectedTags.join(', ');
    } else {
      this.tagsHeader += this.deselectedTags.join(', ');
    }

    if (this.selectedTags.length === 0 && this.deselectedTags.length === 0) {
      this.tagsHeader = '';
    }
  }

  public updateFamiliesCount(): void {
    this.familiesCount = 0;
    this.currentPedigreeTable.pedigrees.forEach(pedigrees => {
      pedigrees.forEach(pedigree => {
        if (pedigree) {
          this.familiesCount += Number(pedigree.count);
        }
      });
    });
  }

  public openModal(): void {
    this.orderedTagList = this.tags;
    if (this.modalService.hasOpenModals()) {
      return;
    }
    this.modal = this.modalService.open(
      this.tagsModal,
      {animation: false, centered: true, windowClass: 'tags-modal'}
    );
  }

  public clearFilters(): void {
    this.selectedTags = [];
    this.deselectedTags = [];
    this.tagsHeader = '';
    this.filtersButtonsState = _.mapValues(this.filtersButtonsState, () => 0);
    this.updateTagFilters();
  }

  public updatePedigrees(newCounters: Dictionary<PedigreeCounter[]>): void {
    for (const table of this.pedigreeTables) {
      table.pedigrees = this.chunkPedigrees(newCounters[table.groupName]);
    }
  }

  public updateTagFilters(): void {
    const copiedCounters = this.copyOriginalPedigreeCounters();
    const filteredCounters = {};
    for (const [groupName, counters] of Object.entries(copiedCounters)) {
      console.log(counters);

      filteredCounters[groupName] =
        counters.filter(x => {
          if (this.tagIntersection) {
            return this.selectedTags.every(v => x.tags.includes(v))
            && this.deselectedTags.every(v => !x.tags.includes(v));
          } else if (this.selectedTags.length || this.deselectedTags.length) {
            return this.selectedTags.some(v => x.tags.includes(v))
            || this.deselectedTags.some(v => !x.tags.includes(v));
          }
          return true;
        });
    }
    this.updatePedigrees(filteredCounters);
  }

  public calculateDenovoVariantsTableWidth(): void {
    if (!this.currentDenovoReport) {
      return;
    }

    const viewWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const tableWidth =
      (this.currentDenovoReport.columns.length * this.denovoVariantsTableColumnWidth)
      + this.denovoVariantsTableColumnWidth;
    const offset = 75;

    this.denovoVariantsTableWidth = viewWidth > tableWidth ? viewWidth - offset : tableWidth;
  }

  public getRows(effectGroups: string[], effectTypes: string[]): string[] {
    let result: string[] = [];

    if (effectGroups) {
      result = effectGroups.concat(effectTypes);
    } else if (effectTypes) {
      result = effectTypes;
    }

    return result;
  }

  public getEffectTypeOrderByColumOrder(
    effectTypeName: string,
    table: EffectTypeTable,
    phenotypes: string[]
  ): DeNovoData[] {
    const effectType = table.rows.find(et => et.effectType === effectTypeName);
    if (!effectType) {
      return [];
    }
    return this.orderByColumnOrder(effectType.data, phenotypes);
  }

  public getDownloadLink(): string {
    return this.variantReportsService.getDownloadLink();
  }

  public downloadTags(event): void {
    let body = {};
    if (this.selectedTags.length || this.deselectedTags.length) {
      body = {
        tagsQuery: {
          orMode: !this.tagIntersection,
          includeTags: this.selectedTags,
          excludeTags: this.deselectedTags
        }
      };
    }

    /* eslint-disable @typescript-eslint/no-unsafe-member-access */
    event.target.queryData.value = JSON.stringify(body);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call
    event.target.submit();
    /* eslint-enable */
  }

  private orderByColumnOrder(childrenCounters: DeNovoData[], columns: string[], strict = false): DeNovoData[] {
    const columnsLookup = new Map<string, number>(
      columns.map((value, index): [string, number] => [value, index])
    );

    const filteredChildrenCounters = childrenCounters.filter(
      childCounters => columnsLookup.has(childCounters.column)
    );

    if (strict && filteredChildrenCounters.length !== columns.length) {
      return [];
    }

    return filteredChildrenCounters.sort(
      (child1, child2) => {
        const index1 = columnsLookup.get(child1.column);
        const index2 = columnsLookup.get(child2.column);
        return index1 - index2;
      }
    );
  }

  private chunkPedigrees(pedigreeCounters: PedigreeCounter[], chunkSize = 4): PedigreeCounter[][] {
    const allPedigrees = pedigreeCounters;

    return allPedigrees.reduce(
      (acc: PedigreeCounter[][], pedigree, index) => {
        if (acc.length === 0 || acc[acc.length - 1].length === chunkSize) {
          acc.push([pedigree]);
        } else {
          acc[acc.length - 1].push(pedigree);
        }

        if (index === allPedigrees.length - 1) {
          const lastChunk = acc[acc.length - 1];
          const toFill = chunkSize - lastChunk.length;
          for (let i = 0; i < toFill; i++) {
            lastChunk.push(null);
          }
        }

        return acc;
      }, []
    );
  }
}
