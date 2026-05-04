import { Component, OnChanges, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { selectUniqueFamilyVariantsFilter, setUniqueFamilyVariantsFilter } from './unique-family-variants-filter.state';
import { Validate, IsDefined } from 'class-validator';
import { DatasetsService } from 'app/datasets/datasets.service';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { take } from 'rxjs';

@Component({
  selector: 'gpf-unique-family-variants-filter',
  templateUrl: './unique-family-variants-filter.component.html',
  styleUrls: ['./unique-family-variants-filter.component.css'],
  standalone: false
})
export class UniqueFamilyVariantsFilterComponent implements OnChanges, OnInit {
  @Validate(IsDefined, {message: 'Must have a boolean value.'})
  private enabled = false;
  public isVisible = false;

  public constructor(
    protected store: Store,
    public datasetService: DatasetsService,
    private datasetsTreeService: DatasetsTreeService
  ) {
  }

  public ngOnChanges(): void {
    this.store.select(selectUniqueFamilyVariantsFilter).pipe(take(1)).subscribe(uniqueFamilyVariantsFilter => {
      this.enabled = uniqueFamilyVariantsFilter;
    });
  }

  public ngOnInit(): void {
    // restore state
    this.store.select(selectUniqueFamilyVariantsFilter).subscribe(state => {
      this.enabled = state;
    });

    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    this.store.select(selectDatasetId).subscribe(async datasetId => {
      const childLeaves = await this.datasetsTreeService.getUniqueLeafNodes(datasetId);
      if (childLeaves.size > 1) {
        this.isVisible = true;
      }
    });
  }

  public get filterValue(): boolean {
    return this.enabled;
  }

  public set filterValue(value: boolean) {
    this.enabled = value;
    this.store.dispatch(setUniqueFamilyVariantsFilter({ uniqueFamilyVariantsFilter: this.enabled }));
  }
}
