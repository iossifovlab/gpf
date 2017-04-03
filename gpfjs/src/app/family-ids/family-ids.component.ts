import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'gpf-family-ids',
  templateUrl: './family-ids.component.html',
  styleUrls: ['./family-ids.component.css']
})
export class FamilyIdsComponent implements OnInit {

  constructor() { }

  ngOnInit() {
  }

  set familyIds(regionsFilter: string) {

  }

  get familyIds() {
    return ""
  }

}
