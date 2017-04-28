import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params, Router } from '@angular/router';

import { Observable } from 'rxjs';
import { BehaviorSubject } from 'rxjs/BehaviorSubject';

import { PhenoBrowserService } from './pheno-browser.service';
import { PhenoInstruments, PhenoInstrument, PhenoMeasures } from './pheno-browser';

@Component({
  selector: 'gpf-pheno-browser',
  templateUrl: './pheno-browser.component.html',
  styleUrls: ['./pheno-browser.component.css']
})
export class PhenoBrowserComponent implements OnInit {

  selectedChanges$: BehaviorSubject<PhenoInstrument> = new BehaviorSubject<PhenoInstrument>(undefined);
  measuresToShow$: Observable<PhenoMeasures>;

  private datasetId: string;
  instruments: Observable<PhenoInstruments>;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private phenoBrowserService: PhenoBrowserService
  ) { }

  ngOnInit() {
    this.route.parent.params.take(1).subscribe(
      (params: Params) => {
        this.datasetId = params['dataset'];
        this.initInstruments(this.datasetId);
      }
    );
    this.measuresToShow$ = this.selectedChanges$
      .switchMap((newSelection) => this.phenoBrowserService.getMeasures(this.datasetId, newSelection))
      .share();
  }

  initInstruments(datasetId: string): void {
    this.instruments = this.phenoBrowserService
      .getInstruments(datasetId).share();

    this.instruments.take(1).subscribe((phenoInstruments) => {
      this.emitInstrument(phenoInstruments.default);
    });
  }

  emitInstrument(instrument: PhenoInstrument) {
    this.selectedChanges$.next(instrument);
  }

  minDomainComparator(a: any, b: any): number {
    let leftVal = a.valuesDomain[0];
    let rightVal = b.valuesDomain[0];

    return PhenoBrowserComponent.compare(leftVal, rightVal);
  }
  maxDomainComparator(a: any, b: any): number {
    let leftVal = a.valuesDomain[1];
    let rightVal = b.valuesDomain[1];

    return PhenoBrowserComponent.compare(leftVal, rightVal);
  }

  static compare(leftVal: any, rightVal:any): number {
    if (leftVal == null && rightVal == null) return 0;
    if (leftVal == null) return -1;
    if (rightVal == null) return 1;

    if (!isNaN(leftVal) && !isNaN(rightVal)) {
      return +leftVal - +rightVal;
    }

    return leftVal.localeCompare(rightVal);
  }
}
