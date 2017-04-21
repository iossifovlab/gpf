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

  private objects: FamilyObjectArray;
  private inView: boolean;
  private familyObjectArray: Observable<FamilyObjectArray>;

  constructor(
    private store: Store<any>,
    private familyCountersService: FamilyCountersService
  ) {
  }

  ngAfterViewInit() {
    this.inView = true;
    this.familyObjectArray = this.store
      .takeWhile(() => this.inView)
      .debounceTime(300)
      .switchMap(() => this.familyCountersService.getCounters(this.genotypeBrowserState));
  }

  shouldInvert(familyObject: FamilyObject): boolean {
    return familyObject.color !== '#ffffff' && familyObject.color !== '#e3d252';
  }

}
