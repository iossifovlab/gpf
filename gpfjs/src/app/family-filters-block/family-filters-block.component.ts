import { Component, AfterViewInit, Input, ViewChild, OnInit, HostListener } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store } from '@ngrx/store';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { FamilyCounter, PedigreeCounter, VariantReport } from 'app/variant-reports/variant-reports';
import { combineLatest, switchMap, take } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { resetFamilyIds, selectFamilyIds } from 'app/family-ids/family-ids.state';
import { resetFamilyTags, selectFamilyTags } from 'app/family-tags/family-tags.state';
import { resetFamilyFilterStates, selectPersonFilters } from 'app/person-filters/person-filters.state';
import {
  resetFamilyMeasureHistograms,
  selectFamilyMeasureHistograms
} from 'app/person-filters-selector/measure-histogram.state';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
  standalone: false
})
export class FamilyFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showAdvancedButton: boolean;
  public showPhenoMeasuresButton: boolean;
  public hasContent = false;

  public tags: Array<string> = new Array<string>();
  public orderedTagList = [];
  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public tagIntersection = true; // mode "And"
  public numOfCols: number;
  public familiesCounters: FamilyCounter[];
  public selectedFamiliesCount: number;
  public showSelectedFamilies = true;

  public constructor(
    private store: Store,
    private variantReportsService: VariantReportsService,
  ) { }

  public ngOnInit(): void {
    this.showAdvancedButton =
      this.dataset.genotypeBrowserConfig.familyFilters.length !== 0 ||
      this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;

    this.showPhenoMeasuresButton = this.dataset.genotypeBrowserConfig.hasFamilyPhenoFilters;

    if (this.variantReportsService.getTags() !== undefined) {
      this.variantReportsService.getTags().subscribe(data => {
        Object.values(data).forEach((tag: string) => {
          this.tags.push(tag);
          this.orderedTagList.push(tag);
        });
        // Calculate grid for the tags
        this.onResize();
      });
    }

    this.store.select(selectDatasetId).pipe(
      take(1),
      switchMap(selectDatasetIdState => {
        const selectedDatasetId = selectDatasetIdState;
        return this.variantReportsService.getVariantReport(selectedDatasetId).pipe(take(1));
      }),
    ).subscribe({
      next: (variantReport: VariantReport) => {
        this.familiesCounters = variantReport.familyReport.familiesCounters;
        this.setFamiliesCount();
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 404) {
          this.showSelectedFamilies = false;
        } else {
          // eslint-disable-next-line @typescript-eslint/only-throw-error
          throw err;
        }
      }
    });
  }

  @HostListener('window:resize')
  public onResize(): void {
    const containerWidth = document.getElementsByClassName('family-filters-block')[0]?.clientWidth;
    this.numOfCols = Math.floor(Math.sqrt(containerWidth/(2.4*this.tags.length)) - 1);
  }

  public ngAfterViewInit(): void {
    this.store.select(selectFamilyIds).pipe(take(1)).subscribe(familyIds => {
      if (familyIds.length !== 0) {
        setTimeout(() => {
          this.ngbNav.select('familyIds');
          this.hasContent = true;
        });
      }
    });

    combineLatest([
      this.store.select(selectFamilyIds),
      this.store.select(selectFamilyTags),
      this.store.select(selectPersonFilters),
      this.store.select(selectFamilyMeasureHistograms),
    ]).pipe(take(1)).subscribe(([familyIdsState, familyTagsState, personFiltersState, familyMeasureHistograms]) => {
      if (familyIdsState.length) {
        setTimeout(() => {
          this.ngbNav.select('familyIds');
          this.hasContent = true;
        });
      } else if (
        familyTagsState.selectedFamilyTags.length
        || familyTagsState.deselectedFamilyTags.length
        || !familyTagsState.tagIntersection
      ) {
        setTimeout(() => {
          this.ngbNav.select('familyTags');
          this.hasContent = true;
        });
      } else if (personFiltersState?.familyFilters?.length) {
        setTimeout(() => {
          this.ngbNav.select('advanced');
          this.hasContent = true;
        });
      } else if (familyMeasureHistograms?.length) {
        setTimeout(() => {
          this.ngbNav.select('phenoMeasures');
          this.hasContent = true;
        });
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(resetFamilyTags());
    this.store.dispatch(resetFamilyIds());
    this.store.dispatch(resetFamilyFilterStates());
    this.store.dispatch(resetFamilyMeasureHistograms());
  }

  public updateTags(tags: {selected: string[]; deselected: string[]}): void {
    this.selectedTags = tags.selected;
    this.deselectedTags = tags.deselected;
    this.setFamiliesCount();
  }

  public updateMode(isIntersected: boolean): void {
    this.tagIntersection = isIntersected;
    this.setFamiliesCount();
  }

  public setFamiliesCount(): void {
    const pedigrees = this.familiesCounters?.map(f => f.pedigreeCounters);
    if (pedigrees) {
      let filteredCounters = new Array<PedigreeCounter>();
      this.selectedFamiliesCount = 0;
      for (const pedigree of pedigrees) {
        filteredCounters = pedigree.filter(x => {
          if (this.tagIntersection) {
            return this.selectedTags.every(v => x.tags.includes(v))
            && this.deselectedTags.every(v => !x.tags.includes(v));
          } else if (this.selectedTags.length || this.deselectedTags.length) {
            return this.selectedTags.some(v => x.tags.includes(v))
            || this.deselectedTags.some(v => !x.tags.includes(v));
          }
          return true;
        });
      }

      filteredCounters.forEach((counter: PedigreeCounter) => {
        this.selectedFamiliesCount += Number(counter.count);
      });
    }
  }
}
