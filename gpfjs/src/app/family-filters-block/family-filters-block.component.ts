import { Component, AfterViewInit, Input, ViewChild, OnInit, HostListener } from '@angular/core';
import { Dataset } from '../datasets/datasets';
import { Store, Selector } from '@ngxs/store';
import { FamilyIdsModel, FamilyIdsState } from 'app/family-ids/family-ids.state';
import { PersonFiltersModel, PersonFiltersState, SetFamilyFilters } from 'app/person-filters/person-filters.state';
import { StateReset } from 'ngxs-reset-plugin';
import { NgbNav } from '@ng-bootstrap/ng-bootstrap';
import { VariantReportsService } from 'app/variant-reports/variant-reports.service';
import { FamilyTagsModel, FamilyTagsState, SetFamilyTags } from 'app/family-tags/family-tags.state';
import { FamilyCounter, PedigreeCounter, VariantReport } from 'app/variant-reports/variant-reports';
import { take } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';

@Component({
  selector: 'gpf-family-filters-block',
  templateUrl: './family-filters-block.component.html',
  styleUrls: ['./family-filters-block.component.css'],
})
export class FamilyFiltersBlockComponent implements OnInit, AfterViewInit {
  @Input() public dataset: Dataset;
  @Input() public genotypeBrowserState: object;
  @ViewChild('nav') public ngbNav: NgbNav;
  public showFamilyTypeFilter: boolean;
  public showAdvancedButton: boolean;
  public hasContent = false;

  public tags: Array<string> = new Array<string>();
  public orderedTagList = [];
  public selectedTags: string[] = [];
  public deselectedTags: string[] = [];
  public tagIntersection = true; // mode "And"
  public numOfCols: number;
  public familiesCounters: FamilyCounter[];
  public familiesCount: number;

  public constructor(
    private store: Store,
    private variantReportsService: VariantReportsService,
    private datasetsService: DatasetsService
  ) { }

  public ngOnInit(): void {
    this.showFamilyTypeFilter = this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;
    this.showAdvancedButton =
      this.dataset.genotypeBrowserConfig.familyFilters.length !== 0 ||
      this.dataset.genotypeBrowserConfig.hasFamilyStructureFilter;

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


    const selectedDataset = this.datasetsService.getSelectedDataset();
    this.variantReportsService.getVariantReport(selectedDataset.id)
      .pipe(take(1))
      .subscribe((variantReport: VariantReport) => {
        this.familiesCounters = variantReport.familyReport.familiesCounters;
        this.setFamiliesCount();
      });
  }

  @HostListener('window:resize')
  public onResize(): void {
    const containerWidth = document.getElementsByClassName('family-filters-block')[0].clientWidth;
    this.numOfCols = Math.floor(Math.sqrt(containerWidth/(2.4*this.tags.length)) - 1);
  }

  public ngAfterViewInit(): void {
    this.store.selectOnce(FamilyFiltersBlockComponent.familyFiltersBlockState).subscribe(state => {
      if (state['familyIds']) {
        setTimeout(() => {
          this.ngbNav.select('familyIds');
          this.hasContent = true;
        });
      } else if (state['selectedFamilyTags'] || state['deselectedFamilyTags'] || state['tagIntersection']) {
        setTimeout(() => {
          this.ngbNav.select('familyTags');
          this.hasContent = true;
        });
      } else if (state['familyFilters']) {
        setTimeout(() => {
          this.ngbNav.select('advanced');
          this.hasContent = true;
        });
      }
    });
  }

  public onNavChange(): void {
    this.store.dispatch(new SetFamilyFilters([]));
    this.store.dispatch(new StateReset(FamilyIdsState));
    this.store.dispatch(new SetFamilyTags([], [], true));
  }

  public updateTags(tags: {selected: string[]; deselected: string[]}): void {
    this.selectedTags = tags.selected;
    this.deselectedTags = tags.deselected;
    this.setFamiliesCount();
  }

  public setFamiliesCount(): void {
    const pedigrees = this.familiesCounters?.map(f => f.pedigreeCounters);
    if (pedigrees) {
      let filteredCounters = new Array<PedigreeCounter>();
      this.familiesCount = 0;
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
        this.familiesCount += Number(counter.count);
      });
    }
  }

  @Selector([FamilyIdsState, FamilyTagsState, PersonFiltersState])
  public static familyFiltersBlockState(
    familyIdsState: FamilyIdsModel, familyTagsState: FamilyTagsModel, personFiltersState: PersonFiltersModel
  ): object {
    const res = {};
    if (familyIdsState.familyIds.length) {
      res['familyIds'] = familyIdsState.familyIds;
    }
    if (familyTagsState.selectedFamilyTags.length) {
      res['selectedFamilyTags'] = familyTagsState.selectedFamilyTags;
    }
    if (familyTagsState.deselectedFamilyTags.length) {
      res['deselectedFamilyTags'] = familyTagsState.deselectedFamilyTags;
    }
    if (!familyTagsState.tagIntersection) {
      res['tagIntersection'] = familyTagsState.tagIntersection;
    }
    if (personFiltersState.familyFilters.length) {
      res['familyFilters'] = personFiltersState.familyFilters;
    }
    return res;
  }
}
