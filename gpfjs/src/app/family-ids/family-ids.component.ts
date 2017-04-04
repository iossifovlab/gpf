import { Component, OnInit, forwardRef } from '@angular/core';
import { QueryStateProvider } from '../query/query-state-provider'

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => FamilyIdsComponent) }]
})
export class FamilyIdsComponent extends QueryStateProvider implements OnInit {
  flashingAlert = false;
  errors: string[];

  constructor() {
    super();
  }

  ngOnInit() {
  }

  set familyIds(regionsFilter: string) {

  }

  get familyIds() {
    return ""
  }

}
