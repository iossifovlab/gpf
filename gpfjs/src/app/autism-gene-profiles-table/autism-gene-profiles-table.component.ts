import {
  Component, ElementRef, EventEmitter, HostListener,
  Input, OnInit, Output, QueryList, Renderer2, ViewChild, ViewChildren
} from '@angular/core';
import {
  AgpConfig, AgpDataset, AgpGene,
  AgpGeneSetsCategory, AgpGenomicScoresCategory, AgpDatasetStatistic,
  AgpDatasetPersonSet
} from './autism-gene-profile-table';
// eslint-disable-next-line no-restricted-imports
import { Subject } from 'rxjs';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { AutismGeneProfileSingleViewComponent } from 'app/autism-gene-profiles-single-view/autism-gene-profile-single-view.component';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { sprintf } from 'sprintf-js';
import { QueryService } from 'app/query/query.service';
import { Store } from '@ngxs/store';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css'],
})
export class AutismGeneProfilesTableComponent implements OnInit {
  @Input() public config: AgpConfig;
  @Output() public createTabEvent = new EventEmitter();

  @ViewChild('geneSearchInput') public geneSearchInput: ElementRef;
  @ViewChildren('columnFilteringButton') public columnFilteringButtons: QueryList<ElementRef>;
  @ViewChildren('dropdownSpan') public dropdownSpans: QueryList<ElementRef>;
  @ViewChildren(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu[];
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];
  @ViewChildren(MultipleSelectMenuComponent) public multipleSelectMenuComponents: QueryList<MultipleSelectMenuComponent>;

  public genes: AgpGene[] = [];

  private pageIndex = 1;
  private loadMoreGenes = true;
  private scrollLoadThreshold = 1000;

  public geneInput: string;
  public searchKeystrokes$: Subject<string> = new Subject();

  public sortBy: string;
  public orderBy: string;
  public currentSortingColumnId: string;
  public modalBottom: number;

  public highlightedRowElements = [];

  // FIXME Recreate top-level dropdown for column categories

  @HostListener('window:scroll')
  public onWindowScroll() {
    if (!this.ref.nativeElement.hidden) {
      const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
      const totalScrollHeight = document.documentElement.scrollHeight;

      if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
        this.updateGenes();
      }
      this.updateModalBottom();
    }
  }

  @HostListener('window:resize')
  public onResize() {
    if (!this.ref.nativeElement.hidden) {
      this.updateModalBottom();
    }
  }

  @HostListener('document:keydown.escape', ['$event'])
  public clearHighlightedRows($event) {
    if ($event.target['localName'] === 'input' || $event.target['localName'] === 'button') {
      return;
    }

    for (const row of this.highlightedRowElements) {
      row.classList.remove('row-highlight');
    }
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private renderer: Renderer2,
    private ref: ElementRef,
    private queryService: QueryService,
    private store: Store,
  ) { }

  public getGeneSetsCategory(id: string): AgpGeneSetsCategory {
    const category = this.config.geneSets.find(cat => cat.category === id);
    return category.defaultVisible ? category : null;
  }

  public getGenomicScoresCategory(id: string): AgpGenomicScoresCategory {
    const category = this.config.genomicScores.find(cat => cat.category === id);
    return category.defaultVisible ? category : null;
  }

  public getDataset(id: string): AgpDataset {
    const dataset = this.config.datasets.find(ds => ds.id === id);
    return dataset.defaultVisible ? dataset : null;
  }

  public ngOnInit(): void {
    this.focusGeneSearchInput();

    this.sortBy = `${this.config.shownGeneSets[0].category}_rank`;
    this.orderBy = 'desc';
    this.currentSortingColumnId = this.sortBy;
    this.autismGeneProfilesService.getGenes(
      this.pageIndex, undefined, this.sortBy, this.orderBy
    ).pipe(take(1)).subscribe(res => {
      this.genes = this.genes.concat(res);
    });

    this.searchKeystrokes$.pipe(
      debounceTime(250),
      distinctUntilChanged()
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });
  }

  public ngAfterViewInit(): void {
    const firstSortingButton = this.sortingButtonsComponents.find(sortingButtonsComponent => {
      return sortingButtonsComponent.id === `${this.config.shownGeneSets[0].category}_rank`;
    });
    setTimeout(() => {
      firstSortingButton.hideState = 1;
      this.updateModalBottom();
    });
  }

  public updateModalBottom(): void {
    const columnFilteringButton = this.columnFilteringButtons.first;
    let result = 0;

    if (columnFilteringButton) {
      result = window.innerHeight - columnFilteringButton.nativeElement.getBoundingClientRect().bottom;
      if (window.innerHeight !== document.documentElement.clientHeight) {
        // if there is a horizontal scroll
        result -= 15;
      }
    }
    this.modalBottom = result;
  }

  public filterGeneSetColumns($event) {
    const menuId = $event.menuId.split(':');
    const category = this.config.geneSets.find(category => category.category === menuId[1]);
    for (const geneSet of category.sets) {
      geneSet.defaultVisible = $event.selected.includes(geneSet.setId);
    }
    if ($event.selected.length === 0) {
      category.defaultVisible = false;
    }
    category.sets.sort((a, b) => $event.order.indexOf(a.setId) - $event.order.indexOf(b.setId));
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterGenomicScoreColumns($event) {
    const menuId = $event.menuId.split(':');
    const category = this.config.genomicScores.find(category => category.category === menuId[1]);
    for (const genomicScore of category.scores) {
      genomicScore.defaultVisible = $event.selected.includes(genomicScore.scoreName);
    }
    if ($event.selected.length === 0) {
      category.defaultVisible = false;
    }
    category.scores.sort((a, b) => $event.order.indexOf(a.scoreName) - $event.order.indexOf(b.scoreName));
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterDatasetColumns($event) {
    const menuId = $event.menuId.split(':');
    const dataset = this.config.datasets.find(dataset => dataset.id === menuId[1]);
    for (const personSet of dataset.personSets) {
      personSet.defaultVisible = $event.selected.includes(personSet.id);
    }
    if ($event.selected.length === 0) {
      dataset.defaultVisible = false;
    }
    dataset.personSets.sort((a, b) => $event.order.indexOf(a.id) - $event.order.indexOf(b.id));
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterPersonSetColumns($event) {
    const menuId = $event.menuId.split(':');
    const personSet = this.config.datasets
      .find(dataset => dataset.id === menuId[1])
      .personSets.find(personSet => personSet.id === menuId[2]);
    for (const statistic of personSet.statistics) {
      statistic.defaultVisible = $event.selected.includes(statistic.id);
    }
    if ($event.selected.length === 0) {
      personSet.defaultVisible = false;
    }
    personSet.statistics.sort((a, b) => $event.order.indexOf(a.id) - $event.order.indexOf(b.id));
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public emitCreateTabEvent($event, geneSymbol: string, navigateToTab: boolean = true): void {
    if ($event.ctrlKey && $event.type === 'click') {
      navigateToTab = false;
    }

    this.createTabEvent.emit({geneSymbol: geneSymbol, navigateToTab: navigateToTab});
  }

  public updateGenes(): void {
    this.loadMoreGenes = false;
    this.pageIndex++;

    this.autismGeneProfilesService
    .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
    .pipe(take(1)).subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = Object.keys(res).length !== 0 ? true : false;
    });
  }

  public search(value: string) {
    this.geneInput = value;
    this.genes = [];
    this.pageIndex = 0;

    this.updateGenes();
  }

  public sendKeystrokes(value: string): void {
    this.searchKeystrokes$.next(value);
  }

  public sort(sortBy: string, orderBy?: string): void {
    if (this.currentSortingColumnId !== sortBy) {
      this.resetSortButtons(sortBy);
    }

    this.sortBy = sortBy;
    if (orderBy) {
      this.orderBy = orderBy;
    }
    this.genes = [];
    this.pageIndex = 0;

    this.updateGenes();
  }

  public resetSortButtons(sortBy: string): void {
    if (this.currentSortingColumnId !== undefined) {
      const sortButton = this.sortingButtonsComponents.find(
        sortingButtonsComponent => {
          return sortingButtonsComponent.id === this.currentSortingColumnId;
        }
      );

      if (sortButton) {
        sortButton.resetHideState();
      }
    }
    this.currentSortingColumnId = sortBy;
  }

  public openGeneSetCategoryDropdown(geneSetCategory: AgpGeneSetsCategory): void {
    this.openDropdown(geneSetCategory.category);
  }

  public openGenomicScoresCategoryDropdown(genomicScoresCategory: AgpGenomicScoresCategory): void {
    this.openDropdown(genomicScoresCategory.category);
  }

  public openDatasetDropdown(dataset: AgpDataset, menuToOpen: string): void {
    this.openDropdown(menuToOpen);
  }

  public async waitForDropdown(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.ngbDropdownMenu !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 15);
    });
  }

  public openDropdown(columnId: string): void {
    this.waitForDropdown().then(() => {
      this.renderer.setStyle(
        this.dropdownSpans.find(ele => ele.nativeElement.id === `${columnId}-span`).nativeElement,
        'left',
        this.calculateModalLeftPosition(
          this.columnFilteringButtons.find(ele => ele.nativeElement.id === `${columnId}-button`).nativeElement
        )
      );
      this.ngbDropdownMenu.find(ele => ele.nativeElement.id === `${columnId}-dropdown`).dropdown.open();
      this.multipleSelectMenuComponents.find(menu => menu.menuId.includes(columnId)).focusSearchInput();
    });
  }

  public calculateModalLeftPosition(columnFilteringButton: HTMLElement): string {
    const modalWidth = 400;
    const leftCap = 30;
    const modalLeft = columnFilteringButton.getBoundingClientRect().right
      - modalWidth
      - document.body.getBoundingClientRect().left;

    return (modalLeft >= leftCap ? modalLeft : leftCap) + 'px';
  }

  public getGeneScoreValue(gene: AgpGene, scoreCategory: string, scoreId: string): string {
    const genomicScore = gene.genomicScores
      .find(score => score.id === scoreCategory).scores
      .find(score => score.id === scoreId);

    return Number(sprintf(genomicScore.format, genomicScore.value)).toString();
  }

  public getEffectTypeValue(gene, datasetId, personSetId, statisticId) {
    return gene.studies.find(study => study.id === datasetId)
      .personSets.find(personSet => personSet.id === personSetId)
      .effectTypes.find(effectType => effectType.id === statisticId)
      .value;
  }

  public calculateDatasetColspan(dataset: AgpDataset): number {
    // TODO Refactor with reduce
    let count = 0;
    dataset.shown.forEach(personSet => count += personSet.shown.length);
    return count;
  }

  public goToQuery(
    geneSymbol: string, personSet: AgpDatasetPersonSet, datasetId: string, statistic: AgpDatasetStatistic
  ): void {
    AutismGeneProfileSingleViewComponent.goToQuery(
      this.store, this.queryService, geneSymbol, personSet, datasetId, statistic
    );
  }

   public async waitForGeneSearchInputToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.geneSearchInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 200);
    });
  }

  public focusGeneSearchInput() {
    this.waitForGeneSearchInputToLoad().then(() => {
      this.geneSearchInput.nativeElement.focus();
    });
  }

  public highlightRow($event): void {
    const linkElements = ['link-td', 'link-span'];
    if (
      (!$event.ctrlKey && $event.type === 'click')
      || linkElements.includes($event.srcElement.classList.value.replace('ng-star-inserted', '').trim())
    ) {
      return;
    }

    let rowElement;
    if ($event.srcElement.parentElement.localName !== 'tr') {
      rowElement = $event.srcElement.parentElement.parentElement
    } else {
      rowElement = $event.srcElement.parentElement;
    }

    rowElement.className.includes('row-highlight')
      ? rowElement.classList.remove('row-highlight')
      : rowElement.classList.add('row-highlight');

    this.highlightedRowElements.push(rowElement);
  }
}
