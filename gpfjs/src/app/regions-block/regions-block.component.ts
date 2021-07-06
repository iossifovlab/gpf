import { Component, ViewChild, AfterViewInit } from '@angular/core';

import { Store } from '@ngxs/store';

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
})
export class RegionsBlockComponent implements AfterViewInit {
  @ViewChild('nav') ngbNav;

  constructor(private store: Store) { }

  ngAfterViewInit() {
    this.store.selectOnce(state => state.regionsFiltersState).subscribe(state => {
      if (state.regionsFilters.length) {
        setTimeout(() => this.ngbNav.select('regionsFilter'));
      }
    });
  }
}
