import { Component, AfterViewInit, Input, ViewChild, OnInit } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store, Selector } from '@ngxs/store';
// import { PersonIdsModel, PersonIdsState } from 'app/person-ids/person-ids.state';
// import { PersonFiltersModel, PersonFiltersState, SetPersonFilters } from 'app/person-filters/person-filters.state';
import { StateReset } from 'ngxs-reset-plugin';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';

@Component({
  selector: 'gpf-person-filters-block',
  templateUrl: './person-filters-block.component.html',
  styleUrls: ['./person-filters-block.component.css'],
})
export class PersonFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @Input() public genotypeBrowserState: object;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showAdvancedButton: boolean;

  public constructor(private store: Store) { }

  public ngOnInit(): void {
    this.showAdvancedButton = this.dataset.genotypeBrowserConfig.personFilters.length !== 0;
  }

  public ngAfterViewInit(): void {
    // this.store.selectOnce(PersonFiltersBlockComponent.personFiltersBlockState).subscribe(state => {
    //   if (state['personIds']) {
    //     setTimeout(() => this.ngbNav.select('personIds'));
    //   } else if (state['personFilters']) {
    //     setTimeout(() => this.ngbNav.select('advanced'));
    //   }
    // });
  }

  public onNavChange(): void {
    // this.store.dispatch(new SetPersonFilters([]));
    // this.store.dispatch(new StateReset(PersonIdsState));
  }
}
