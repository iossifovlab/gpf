import { Component, ViewChild, AfterViewInit, OnInit } from '@angular/core';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { Store } from '@ngrx/store';
import { InstanceService } from 'app/instance.service';
import { resetRegionsFilters, selectRegionsFilters } from 'app/regions-filter/regions-filter.state';
import { take } from 'rxjs';

@Component({
    selector: 'gpf-regions-block',
    templateUrl: './regions-block.component.html',
    styleUrls: ['./regions-block.component.css'],
    standalone: false
})
export class RegionsBlockComponent implements OnInit, AfterViewInit {
  @ViewChild('nav') public ngbNav: NgbNav;
  public genome: string;

  public constructor(
    private store: Store,
    private instanceService: InstanceService,
  ) { }

  public ngOnInit(): void {
    this.instanceService.getGenome().pipe(take(1)).subscribe(res => {
      this.genome = res;
    });
  }

  public ngAfterViewInit(): void {
    this.store.select(selectRegionsFilters).pipe(take(1)).subscribe(regionsFiltersState => {
      if (regionsFiltersState.length) {
        setTimeout(() => this.ngbNav.select('regionsFilter'));
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(resetRegionsFilters());
  }
}
