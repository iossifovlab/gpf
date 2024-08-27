import { Component, ViewChild, AfterViewInit, Input } from '@angular/core';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
// import { RegionsFilterModel, RegionsFilterState } from 'app/regions-filter/regions-filter.state';

@Component({
  selector: 'gpf-regions-block',
  templateUrl: './regions-block.component.html',
  styleUrls: ['./regions-block.component.css'],
})
export class RegionsBlockComponent implements AfterViewInit {
  @ViewChild('nav') public ngbNav: NgbNav;
  @Input() public genome: string;

  public constructor(private store: Store) { }

  public ngAfterViewInit(): void {
    // this.store.selectOnce(RegionsFilterState).subscribe((state: RegionsFilterModel) => {
    //   if (state.regionsFilters.length) {
    //     setTimeout(() => this.ngbNav.select('regionsFilter'));
    //   }
    // });
  }

  public onNavChange(): void {
    // this.store.dispatch(new StateReset(RegionsFilterState));
  }
}
