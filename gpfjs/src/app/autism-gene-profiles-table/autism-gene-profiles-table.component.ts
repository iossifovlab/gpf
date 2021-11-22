import {
  Component, ElementRef, EventEmitter, HostListener,
  Input, OnChanges, OnInit, Output, Pipe, PipeTransform, QueryList, Renderer2, ViewChild, ViewChildren
} from '@angular/core';
import {
  AgpConfig, AgpDataset, AgpGene,
  AgpGeneSetsCategory, AgpGenomicScoresCategory, AgpDatasetStatistic,
  AgpDatasetPersonSet,
  AgpGenomicScore,
  AgpPersonSet
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
import { ItemApplyEvent } from 'app/multiple-select-menu/multiple-select-menu';

@Pipe({name: 'getGeneScore'})
export class GetGeneScorePipe implements PipeTransform {
  transform(gene: AgpGene, scoreCategory: AgpGenomicScoresCategory, score: AgpGenomicScore, args?: any): string {
    const genomicScore = gene.genomicScores
      .find(s => s.id === scoreCategory.category).scores
      .find(s => s.id === score.scoreName);
    return genomicScore.value ? Number(sprintf(genomicScore.format, genomicScore.value)).toString() : '';
  }
}

@Pipe({name: 'getEffectTypeValue'})
export class GetEffectTypeValuePipe implements PipeTransform {
  transform(gene: AgpGene, dataset: AgpDataset, personSet: AgpDatasetPersonSet, statistic: AgpDatasetStatistic, args?: any): string {
    // FIXME Disable link clicking on empty cells somehow without spamming functions in the templates
    const effectTypeValue = gene.studies.find(study => study.id === dataset.id)
      .personSets.find(ps => ps.id === personSet.id)
      .effectTypes.find(effectType => effectType.id === statistic.id)
      .value;
    return effectTypeValue.count ? `${effectTypeValue.count} (${effectTypeValue.rate.toFixed(3)})` : '';
  }
}

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css'],
})
export class AutismGeneProfilesTableComponent implements OnInit, OnChanges {
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
  private scrollLoadThreshold = 100;

  public geneInput: string;
  public searchKeystrokes$: Subject<string> = new Subject();

  public sortBy: string;
  public orderBy: string;
  public currentSortingColumnId: string;
  public modalBottom: number;

  public highlightedRowElements: Element[] = [];
  
  @ViewChild('table') tableViewChild: any;
  @ViewChildren('rows') rowViewChildren: QueryList<any>;

  private lastRowHeight = 35;
  private drawOutsideVisibleCount = 5;
  private tableTopPosition = 0;

  @HostListener('window:scroll')
  public onWindowScroll() {
    this.tableTopPosition = this.tableViewChild.nativeElement.getBoundingClientRect().top;
    if (this.rowViewChildren &&
        this.rowViewChildren.last &&
        this.rowViewChildren.last.nativeElement.getBoundingClientRect().height > 0) {
      this.lastRowHeight = this.rowViewChildren.last.nativeElement.getBoundingClientRect().height;
    }
    if (!this.ref.nativeElement.hidden) {
      const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
      const totalScrollHeight = document.documentElement.scrollHeight;
      // if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
      //   this.updateGenes();
      // }
      const scrollIndices = this.getScrollIndices();
      // console.log(scrollIndices, this.drawOutsideVisibleCount, this.genes.length, (scrollIndices[1] + (this.drawOutsideVisibleCount * 2)));
      if (scrollIndices[1] >= this.genes.length) {
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
  public clearHighlightedRows($event: KeyboardEvent) {
    if($event.target instanceof Element) {
      if ($event.target.localName === 'input' || $event.target.localName === 'button') {
        return;
      }
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

  tableTop(): boolean {
    return this.tableViewChild.nativeElement.getBoundingClientRect().top < 0;
  }

  getScrollIndices(): Array<number> {
    if (!this.genes) {
      return [0, 0];
    }
    const visibleRowCount = Math.ceil(window.innerHeight / this.lastRowHeight);
    const maxRowCountToDraw = (this.drawOutsideVisibleCount * 2) + visibleRowCount;

    // console.log('tabletop', this.tableTopPosition);
    let startIndex = Math.ceil(-this.tableTopPosition / this.lastRowHeight);
    // console.log('startindex', startIndex);

    // We should display at least maxRowCountToDraw rows, even at the bottom of the page
    const maxStartIndex = this.genes.length - maxRowCountToDraw;
    startIndex = Math.min(startIndex, maxStartIndex);

    // Make sure we always start from index 0 or above
    startIndex = Math.max(0, startIndex);

    const endIndex = startIndex + maxRowCountToDraw + 5;
    return [startIndex, endIndex];
  }

  get visibleData(): Array<any> {
    if (!this.genes) {
      return [];
    }
    const scrollIndices = this.getScrollIndices();
    return this.genes.slice(scrollIndices[0], scrollIndices[1] + 5);
  }

  isVisibleData(idx: number): boolean {
    const scrollIndices = this.getScrollIndices();
    return scrollIndices[0] <= idx + 10 && idx - 10 <= scrollIndices[1];
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

  public ngOnChanges() {
    this.setupShownCategories();
    for (const dataset of this.config.datasets) {
      this.calculateDatasetColspan(dataset);
    }
  }

  public ngAfterViewInit(): void {
    const firstSortingButton = this.sortingButtonsComponents.find(sortingButtonsComponent => {
      return sortingButtonsComponent.id === `${this.config.shownGeneSets[0].category}_rank`;
    });
    setTimeout(() => {
      firstSortingButton.hideState = 1;
      this.updateModalBottom();
      this.tableTopPosition = this.tableViewChild.nativeElement.getBoundingClientRect().top;
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

  public filterGeneSetColumns($event: ItemApplyEvent) {
    const menuId = $event.menuId.split(':');
    const category = this.config.geneSets.find(category => category.category === menuId[1]);
    for (const geneSet of category.sets) {
      geneSet.defaultVisible = $event.selected.includes(geneSet.setId);
    }
    category.defaultVisible = $event.selected.length > 0;
    category['shown'] = category.sets.filter(set => set.defaultVisible);
    category.sets.sort((a, b) => $event.order.indexOf(a.setId) - $event.order.indexOf(b.setId));
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterGenomicScoreColumns($event: ItemApplyEvent) {
    const menuId = $event.menuId.split(':');
    const category = this.config.genomicScores.find(category => category.category === menuId[1]);
    for (const genomicScore of category.scores) {
      genomicScore.defaultVisible = $event.selected.includes(genomicScore.scoreName);
    }
    category.defaultVisible = $event.selected.length > 0;
    category['shown'] = category.scores.filter(score => score.defaultVisible);
    category.scores.sort((a, b) => $event.order.indexOf(a.scoreName) - $event.order.indexOf(b.scoreName));
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterDatasetColumns($event: ItemApplyEvent) {
    const menuId = $event.menuId.split(':');
    const dataset = this.config.datasets.find(dataset => dataset.id === menuId[1]);
    for (const personSet of dataset.personSets) {
      personSet.defaultVisible = $event.selected.includes(personSet.id);
      if (personSet.defaultVisible && !personSet.shownItemIds.length) {
        personSet.statistics.forEach(s => s.defaultVisible = true);
      }
    }
    dataset.defaultVisible = $event.selected.length > 0;
    dataset['shown'] = dataset.personSets.filter(set => set.defaultVisible);
    dataset.personSets.sort((a, b) => $event.order.indexOf(a.id) - $event.order.indexOf(b.id));
    this.calculateDatasetColspan(dataset);
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterPersonSetColumns($event: ItemApplyEvent) {
    const menuId = $event.menuId.split(':');
    const dataset = this.config.datasets.find(dataset => dataset.id === menuId[1])
    const personSet = dataset.personSets.find(personSet => personSet.id === menuId[2]);
    for (const statistic of personSet.statistics) {
      statistic.defaultVisible = $event.selected.includes(statistic.id);
    }
    personSet.defaultVisible = $event.selected.length > 0;
    dataset.defaultVisible = dataset.shownItemIds.length > 0;
    this.calculateDatasetColspan(dataset);
    personSet.statistics.sort((a, b) => $event.order.indexOf(a.id) - $event.order.indexOf(b.id));
    personSet['shown'] = personSet.statistics.filter(s => s.defaultVisible);
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public filterCategories($event: ItemApplyEvent) {
    for (const category of this.config.categories) {
      category.defaultVisible = $event.selected.includes(category.id);
      if (category.defaultVisible && !category.shownItemIds.length) {
        category.items.forEach(item => item.defaultVisible = true);
        if (category instanceof AgpDataset) {
          category['personSets'].forEach(ps => ps.statistics.forEach(s => {
            s.defaultVisible = true;
          }));
          this.calculateDatasetColspan(category as AgpDataset);
        }
      }
    }
    this.config.order.sort((a, b) => $event.order.indexOf(a.id) - $event.order.indexOf(b.id));
    this.setupShownCategories();
    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  public setupShownCategories() {
    this.config['shown'] = [];
    for (const item of this.config.order) {
      let category;
      switch(item.section) {
        case 'geneSets':
          category = this.config.geneSets.find(gs => gs.category === item.id);
          category['shown'] = category.sets.filter(set => set.defaultVisible);
          break;
        case 'genomicScores':
          category = this.config.genomicScores.find(gs => gs.category === item.id)
          category['shown'] = category.scores.filter(score => score.defaultVisible);
          break;
        case 'datasets':
          category = this.config.datasets.find(ds => ds.id === item.id)
          category['shown'] = category.personSets.filter(set => set.defaultVisible);
          for (const personSet of category.personSets) {
            personSet['shown'] = personSet.statistics.filter(s => s.defaultVisible);
          }
          break;
      }
      this.config['shown'].push({...item, category: category});
    }
  }

  public emitCreateTabEvent($event: MouseEvent, geneSymbol: string, navigateToTab: boolean = true): void {
    if ($event.ctrlKey && $event.type === 'click') {
      navigateToTab = false;
    }
    this.createTabEvent.emit({geneSymbol: geneSymbol, navigateToTab: navigateToTab});
  }

  public updateGenes(): void {
    console.log('loading more genes');
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
      this.multipleSelectMenuComponents.find(menu => menu.menuId.includes(columnId)).refresh();
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

  public calculateDatasetColspan(dataset: AgpDataset): void {
    dataset['colspan'] = dataset['shown']
      .map(personSet => personSet.shown.length)
      .reduce((sum, length) => sum += length, 0);
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

  public highlightRow($event: MouseEvent): void {
    if(!($event.target instanceof Element)) {
      return;
    }

    const linkElements = ['link-td', 'link-span'];
    if (
      !$event.ctrlKey && $event.type === 'click'
      || linkElements.includes($event.target.classList.value.replace('ng-star-inserted', '').trim())
    ) {
      return;
    }

    let rowElement: Element;
    if ($event.target.parentElement.localName !== 'tr') {
      rowElement = $event.target.parentElement.parentElement
    } else {
      rowElement = $event.target.parentElement;
    }

    rowElement.className.includes('row-highlight')
      ? rowElement.classList.remove('row-highlight')
      : rowElement.classList.add('row-highlight');

    this.highlightedRowElements.push(rowElement);
  }
}
