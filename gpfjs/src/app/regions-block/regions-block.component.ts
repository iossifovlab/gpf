import { Component, ViewChild, AfterViewInit } from '@angular/core';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngxs/store';
import { RegionsFilterState } from 'app/regions-filter/regions-filter.state';
import { StateReset } from 'ngxs-reset-plugin';

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
})
export class RegionsBlockComponent implements AfterViewInit {
  @ViewChild('nav') public ngbNav: NgbNav;

  public constructor(private store: Store) { }

  public ngAfterViewInit(): void {
    this.store.selectOnce(RegionsFilterState).subscribe(state => {
      if (state.regionsFilters.length) {
        setTimeout(() => this.ngbNav.select('regionsFilter'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new StateReset(RegionsFilterState));
  }
}
