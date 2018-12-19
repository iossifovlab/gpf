import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import { Observable, Subject } from 'rxjs';

import { VariantReportsService } from './variant-reports.service';
import { Studies, Study, VariantReport, ChildrenCounter,
         FamilyCounter, PedigreeCounter, EffectTypeTable, DeNovoData,
         PedigreeTable, PeopleCounter
        } from './variant-reports';

export const SELECTED_REPORT_QUERY_PARAM = 'selectedReport';

@Component({
  selector: 'gpf-variant-reports',
  templateUrl: './variant-reports.component.html',
  styleUrls: ['./variant-reports.component.css']
})
export class VariantReportsComponent implements OnInit {


  reports$: Observable<Studies>;
  selectedReport$ = new Subject<Study>();

  peopleCounter: PeopleCounter;
  pedigreeTable: PedigreeTable;
  denovoReport: EffectTypeTable;

  variantReport$: Observable<VariantReport>;
  pedigreeTables: PedigreeTable[];

  constructor(
    private variantReportsService: VariantReportsService,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit() {
    this.reports$ = this.variantReportsService.getStudies().share();

    this.variantReport$ = this.selectedReport$
      .switchMap(study => this.variantReportsService.getVariantReport(study))
      .do(study => this.setSelectedReportParam(study.studyName))
      .share();

    this.variantReport$.take(1).subscribe(params => {
      this.pedigreeTables = params.familyReport.familiesCounters.map(
        familiesCounters => new PedigreeTable(
            this.chunkPedigrees(familiesCounters.familyCounter),
            familiesCounters.phenotypes, familiesCounters.groupName
          )
        );
    });

    this.loadReportFromParams();
  }

  private setSelectedReportParam(studyName) {
    this.route.params
      .take(1)
      .subscribe(params => {
        if (!params[SELECTED_REPORT_QUERY_PARAM] ||
          params[SELECTED_REPORT_QUERY_PARAM] !== studyName) {
            let param = {};
            param[SELECTED_REPORT_QUERY_PARAM] = studyName;

            this.router.navigate(['/reports/reports', param]);
          }
      });
  }

  private loadReportFromParams() {
    Observable.combineLatest([
        this.reports$,
        this.route.params
      ])
      .take(1)
      .subscribe(([reports, params]) => {
        if (params[SELECTED_REPORT_QUERY_PARAM]) {
          let report = reports.studies
            .find(study => study.name === params[SELECTED_REPORT_QUERY_PARAM]);
          if (report) {
            this.selectReport(report);
          }
        }
      });

  }

  selectReport(study: Study) {
    this.selectedReport$.next(study);

    this.variantReport$.take(1).subscribe(params => {
      this.pedigreeTables = params.familyReport.familiesCounters.map(
        familiesCounters => {
          return {
            'pedigrees': this.chunkPedigrees(familiesCounters.familyCounter),
            'phenotypes': familiesCounters.phenotypes,
            'groupName': familiesCounters.groupName
          };
        });
    });
  }

  set selectedPeopleCounter(peopleCounter: PeopleCounter) {
    this.peopleCounter = peopleCounter;
  }

  get selectedPeopleCounter() {
    return this.peopleCounter;
  }

  set selectedPedigreeTable(pedigreeTable: PedigreeTable) {
    this.pedigreeTable = pedigreeTable;
  }

  get selectedPedigreeTable() {
    return this.pedigreeTable;
  }

  set selectedDenovoReport(denovoReport: EffectTypeTable) {
    this.denovoReport = denovoReport;
  }

  get selectedDenovoReport() {
    return this.denovoReport;
  }

  orderByColumnOrder(childrenCounters: (ChildrenCounter | DeNovoData)[], columns: string[], strict = false) {
    console.log(columns);
    let columnsLookup = new Map<string, number>(
      columns.map((value, index): [string, number] => [value, index])
    );

    let filteredChildrenCounters = childrenCounters
      .filter(
        childCounters => columnsLookup.has(childCounters.column));

    if (strict && filteredChildrenCounters.length !== columns.length) {
      return [];
    }

    return filteredChildrenCounters.sort(
      (child1, child2) => {
        let index1 = columnsLookup.get(child1.column);
        let index2 = columnsLookup.get(child2.column);
        return index1 - index2;
      }
    );
  }

  chunkPedigrees(familyCounters: FamilyCounter[], chunkSize = 4) {
    let allPedigrees = familyCounters
      .reduce(
        (acc, familyCounter) =>
          acc.concat(familyCounter.pedigreeCounters),
        [] as PedigreeCounter[]);

    return allPedigrees
      .reduce(
        (acc: PedigreeCounter[][], pedigree, index) => {
          if (acc.length === 0 || acc[acc.length - 1].length === chunkSize) {
            acc.push([pedigree]);
          } else {
            acc[acc.length - 1].push(pedigree);
          }

          if (index === allPedigrees.length - 1) {
            let lastChunk = acc[acc.length - 1];
            let toFill = chunkSize - lastChunk.length;
            for (let i = 0; i <  toFill; i++) {
              lastChunk.push(null);
            }
          }

          return acc;
        },
        []);

  }

  getRows(effectGroups: string[], effectTypes: string[]) {
    if (effectGroups) {
      return effectGroups.concat(effectTypes);
    } else if (effectTypes) {
      return effectTypes;
    }
    return [];
  }

  getEffectTypeOrderByColumOrder(effectTypeName: string, table: EffectTypeTable, phenotypes: string[]) {
    let effectType = table.rows
      .find(et => et.effectType === effectTypeName);

    if (!effectType) {
      return [];
    }
    return this.orderByColumnOrder(effectType.data, phenotypes);
  }

  getDownloadLink(variantReport: VariantReport) {
    return this.variantReportsService.getDownloadLink(variantReport);
  }

}
