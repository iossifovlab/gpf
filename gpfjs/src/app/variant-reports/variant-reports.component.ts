import { Component, OnInit, ViewChild, ElementRef, HostListener } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { Observable } from 'rxjs';
import { VariantReportsService } from './variant-reports.service';
import { VariantReport, FamilyCounter, PedigreeCounter, EffectTypeTable,
         DeNovoData, PedigreeTable, PeopleCounter, PeopleSex } from './variant-reports';
import { Dataset } from 'app/datasets/datasets';
import { DatasetsService } from 'app/datasets/datasets.service';
import { skipWhile, take } from 'rxjs/operators';

@Component({
  selector: 'gpf-variant-reports',
  templateUrl: './variant-reports.component.html',
  styleUrls: ['./variant-reports.component.css']
})
export class VariantReportsComponent implements OnInit {
  @ViewChild('families_pedigree') private familiesPedigree: ElementRef;
  @ViewChild('legend') private legend: ElementRef;
  public familiesPedigreeTop: number;
  public familiesPedigreeBottom: number;
  public legendTop: number;

  public currentPeopleCounter: PeopleCounter;
  public currentPedigreeTable: PedigreeTable;
  public currentDenovoReport: EffectTypeTable;

  public variantReport: VariantReport;
  public pedigreeTables: PedigreeTable[];

  public selectedDataset: Dataset;

  constructor(
    private variantReportsService: VariantReportsService,
    private datasetsService: DatasetsService,
  ) { }

  public ngOnInit(): void {
    this.selectedDataset = this.datasetsService.getSelectedDataset();
    this.variantReportsService.getVariantReport(this.selectedDataset.id).pipe(take(1)).subscribe(params => {
      this.variantReport = params;
      this.pedigreeTables = this.variantReport.familyReport.familiesCounters.map(
        familiesCounters => new PedigreeTable(
          this.chunkPedigrees(familiesCounters.familyCounter),
          familiesCounters.phenotypes, familiesCounters.groupName,
          familiesCounters.legend
        )
      );

      this.currentPeopleCounter = this.variantReport.peopleReport.peopleCounters[0];
      this.currentPedigreeTable = this.pedigreeTables[0];
      if (this.variantReport.denovoReport !== null) {
        this.currentDenovoReport = this.variantReport.denovoReport.tables[0];
      }
    });
  }

  @HostListener('window:scroll', ['$event'])
  @HostListener('click', ['$event'])
  private onWindowScroll() {
    if (this.familiesPedigree && this.familiesPedigree.nativeElement) {
      this.familiesPedigreeTop = this.familiesPedigree.nativeElement.getBoundingClientRect().top;
      this.familiesPedigreeBottom = this.familiesPedigree.nativeElement.getBoundingClientRect().bottom;
    }

    if (this.legend && this.legend.nativeElement) {
      this.legendTop = this.legend.nativeElement.getBoundingClientRect().top;
    }
  }

  public getPeopleSexValue(peopleSex: string) {
    return PeopleSex[peopleSex];
  }

  private orderByColumnOrder(childrenCounters: DeNovoData[], columns: string[], strict = false) {
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

  private chunkPedigrees(familyCounters: FamilyCounter[], chunkSize = 4) {
    const allPedigrees = familyCounters.reduce(
      (acc, familyCounter) => acc.concat(familyCounter.pedigreeCounters), [] as PedigreeCounter[]
    );

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

  public getRows(effectGroups: string[], effectTypes: string[]) {
    if (effectGroups) {
      return effectGroups.concat(effectTypes);
    } else if (effectTypes) {
      return effectTypes;
    }
    return [];
  }

  public getEffectTypeOrderByColumOrder(effectTypeName: string, table: EffectTypeTable, phenotypes: string[]) {
    const effectType = table.rows.find(et => et.effectType === effectTypeName);
    if (!effectType) {
      return [];
    }
    return this.orderByColumnOrder(effectType.data, phenotypes);
  }

  public getDownloadLink() {
    return this.variantReportsService.getDownloadLink();
  }
}
