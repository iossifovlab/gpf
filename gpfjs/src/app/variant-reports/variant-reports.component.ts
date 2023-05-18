import { Component, OnInit, HostListener, Pipe, PipeTransform, Input } from '@angular/core';
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
import { IDropdownSettings } from 'ng-multiselect-dropdown';

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
  @Input() public isFamiliesByNumberVisible = false;

  public variantReport: VariantReport;
  public familiesCounters: FamilyCounter[];
  public pedigreeTables: PedigreeTable[];

  public selectedDataset: Dataset;

  public imgPathPrefix = environment.imgPathPrefix;
  public dropdownList = [];
  public selectedItems = [];
  public dropdownSettings: IDropdownSettings = {};

  public denovoVariantsTableWidth: number;
  private denovoVariantsTableColumnWidth = 140;

  public constructor(
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
    });
    if (this.variantReportsService.getTags() !== undefined) {
      this.variantReportsService.getTags().subscribe(data => {
        Object.values(data).forEach(tag => {
          this.tags.push(tag);
          this.dropdownList.push(tag);
        });
      });
    }

    this.dropdownSettings = {
      singleSelection: false,
      idField: 'item_id',
      textField: 'item_text',
      selectAllText: 'Select All',
      unSelectAllText: 'UnSelect All',
      allowSearchFilter: true,
      maxHeight: 150
    };
    this.isFamiliesByNumberVisible = true;
  }

  private copyOriginalPedigreeCounters(): Record<string, PedigreeCounter[]> {
    return this.familiesCounters.reduce(
      (obj, x) => {
        obj[x.groupName] = Array.from(x.pedigreeCounters); return obj;
      }, {}
    );
  }

  private getSelectedTags(): string[] {
    return this.tags.filter(x => this.selectedItems.includes(x));
  }

  public updatePedigrees(newCounters: Dictionary<PedigreeCounter[]>): void {
    for (const table of this.pedigreeTables) {
      table.pedigrees = this.chunkPedigrees(newCounters[table.groupName]);
    }
  }

  public updateTagFilters(): void {
    const tags = this.getSelectedTags();
    const copiedCounters = this.copyOriginalPedigreeCounters();
    const filteredCounters = {};
    for (const [groupName, counters] of Object.entries(copiedCounters)) {
      filteredCounters[groupName] = counters.filter(x => _.difference(tags, x.tags).length === 0);
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

  public downloadTags(): void {
    const tags = this.getSelectedTags().join(',');
    location.href = this.variantReportsService.getDownloadLinkTags(tags);
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
