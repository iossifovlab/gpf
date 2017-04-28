import { Component, OnInit, Input, AfterViewInit, OnDestroy } from '@angular/core';

import { Observable } from 'rxjs';
import { Store } from '@ngrx/store';

import { FamilyObjectArray, FamilyObject } from './family-counters';
import { FamilyCountersService } from './family-counters.service';

@Component({
  selector: 'gpf-family-counters',
  templateUrl: './family-counters.component.html',
  styleUrls: ['./family-counters.component.css']
})
export class FamilyCountersComponent implements AfterViewInit {
  @Input() genotypeBrowserState: Object;

  familyObjectArray: Observable<FamilyObjectArray>;

  constructor(
    private store: Store<any>,
    private familyCountersService: FamilyCountersService
  ) {
  }

  ngAfterViewInit() {
    this.familyObjectArray = this.store
      .debounceTime(300)
      .switchMap(() => this.familyCountersService.getCounters(this.genotypeBrowserState));
  }

  shouldInvert(familyObject: FamilyObject): boolean {
    return familyObject.color !== '#ffffff' && familyObject.color !== '#e3d252';
  }

}
