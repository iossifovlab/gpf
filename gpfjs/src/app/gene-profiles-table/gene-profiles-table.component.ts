import {
  Component, ElementRef, EventEmitter, HostListener, Input, OnChanges,
  OnDestroy, OnInit, Output, ViewChild, ViewChildren
} from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { debounceTime, distinctUntilChanged, take, tap } from 'rxjs/operators';
import { Subject, Subscription, zip } from 'rxjs';
import { GeneProfilesTableConfig, GeneProfilesColumn } from './gene-profiles-table';
import { GeneProfilesTableService } from './gene-profiles-table.service';
import { environment } from 'environments/environment';
import { Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { Store } from '@ngxs/store';
import {
  GeneProfilesModel,
  GeneProfilesState,
  SetGeneProfilesHeader,
  SetGeneProfilesHighlightedRows,
  SetGeneProfilesOrderBy,
  SetGeneProfilesSearchValue,
  SetGeneProfilesSortBy,
  SetGeneProfilesTabs } from './gene-profiles-table.state';
import { StatefulComponent } from 'app/common/stateful-component';
import { StateReset } from 'ngxs-reset-plugin';

@Component({
  selector: 'gpf-gene-profiles-table',
  templateUrl: './gene-profiles-table.component.html',
  styleUrls: ['./gene-profiles-table.component.css']
})
export class GeneProfilesTableComponent extends StatefulComponent implements OnInit, OnChanges, OnDestroy {
  @Input() public config: GeneProfilesTableConfig;
  public sortBy: string;
  @Output() public goToQueryEvent = new EventEmitter();
  @Output() public resetConfig = new EventEmitter();

  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild('dropdownSpan') public dropdownSpan: ElementRef;
  @ViewChild(MultipleSelectMenuComponent) public multipleSelectMenuComponent: MultipleSelectMenuComponent;
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];

  private clickedColumnFilteringButton: HTMLElement;
  public modalPosition = {top: 0, left: 0};
  public showKeybinds = false;

  public leaves: GeneProfilesColumn[];
  public leavesIds: string[] = [];
  public genes = [];
  public shownRows: number[] = []; // indexes
  public highlightedGenes: Set<string> = new Set();

  public geneSymbolColumnId = 'geneSymbol'; // must match the gene symbol column id from the backend

  public orderBy = 'desc';

  public geneInput: string = null;
  public loadedSearchValue: string = null;
  public searchKeystrokes$: Subject<string> = new Subject();
  @ViewChild('searchBox') public searchBox: ElementRef;
  public pageIndex = 0;
  public nothingFoundWidth: number;
  public showNothingFound = false;
  public showInitialLoading = true;
  public showSearchLoading: boolean;

  private viewportPageCount: number;
  private baseRowHeight = 35; // px, this should match the height found in the table-row CSS class
  private prevVerticalScroll = 0;
  private loadMoreGenes = true;
  private keystrokeSubscription: Subscription;
  private getGenesSubscription: Subscription = new Subscription();
  public imgPathPrefix = environment.imgPathPrefix;

  public tabs = new Set<string>();
  public hideTable = false;
  public currentTabGeneSet= new Set<string>();
  public currentTabString = 'all genes';

  public stateFinishedLoading = false;

  public constructor(
    private geneProfilesTableService: GeneProfilesTableService,
    private location: Location,
    private route: ActivatedRoute,
    protected store: Store,
  ) {
    super(store, GeneProfilesState, 'geneProfiles');
  }

  public ngOnInit(): void {
    this.keystrokeSubscription = this.searchKeystrokes$.pipe(
      distinctUntilChanged(),
      tap(() => {
        this.showSearchLoading = true;
      }),
      debounceTime(250),
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });

    this.focusSearchBox();

    if (this.route.snapshot.params.genes as string) {
      this.currentTabGeneSet = new Set(
        (this.route.snapshot.params.genes as string)
          .split(',')
          .filter(p => p)
          .map(p => p.trim())
      );
      this.loadSingleView(this.currentTabGeneSet);
    }

    this.loadState();

    this.geneProfilesTableService.getUserGeneProfilesState().subscribe(state => {
      if (state) {
        this.store.dispatch(new SetGeneProfilesTabs(state.openedTabs));
        this.store.dispatch(new SetGeneProfilesSearchValue(state.searchValue));
        this.store.dispatch(new SetGeneProfilesHighlightedRows(state.highlightedRows));
        this.store.dispatch(new SetGeneProfilesSortBy(state.sortBy));
        this.store.dispatch(new SetGeneProfilesOrderBy(state.orderBy));
        this.store.dispatch(new SetGeneProfilesHeader(state.headerLeaves));
        this.loadState();
      }
    });
  }

  public ngOnChanges(): void {
    if (this.stateFinishedLoading) {
      this.resetLeavesIds();
      this.prepareTable();
    }
  }

  public ngOnDestroy(): void {
    this.keystrokeSubscription.unsubscribe();
  }

  @HostListener('document:keydown.esc')
  public keybindClearHighlight(): void {
    if (this.highlightedGenes.size
        && (document.activeElement === document.body || document.activeElement.nodeName === 'BUTTON')) {
      this.highlightedGenes.clear();
    }
  }

  @HostListener('document:keydown.c')
  public keybindCompareGenes(): void {
    if (this.highlightedGenes.size
        && (document.activeElement === document.body || document.activeElement.nodeName === 'BUTTON')) {
      this.loadSingleView(this.highlightedGenes);
    }
  }

  @HostListener('window:scroll', ['$event'])
  public onWindowScroll($event: Event): void {
    if (this.prevVerticalScroll !== ($event.target['scrollingElement'] as HTMLElement).scrollTop) {
      const tableBodyOffset = document.getElementById('table-body').offsetTop;
      const topRowIdx = Math.floor(Math.max(window.scrollY - tableBodyOffset, 0) / this.baseRowHeight);
      const bottomRowIdx = Math.floor(window.innerHeight / this.baseRowHeight) + topRowIdx;
      this.prevVerticalScroll = ($event.target['scrollingElement'] as HTMLElement).scrollTop;
      this.updateShownGenes(topRowIdx - 20, bottomRowIdx + 20);
      if (bottomRowIdx + 40 >= this.genes.length && this.loadMoreGenes) {
        this.updateGenes();
      }
    }

    this.ngbDropdownMenu.dropdown.close();
  }

  @HostListener('window:resize')
  public onResize(): void {
    this.ngbDropdownMenu.dropdown.close();
  }

  private setDefaultSortableCategory(): void {
    this.sortBy = this.config.columns.filter(column => column.sortable)[0].id;
  }

  private prepareTable(): void {
    this.viewportPageCount = Math.ceil(window.innerHeight / (this.baseRowHeight * this.config.pageSize));
    this.setLeavesVisibility();
    this.calculateHeaderLayout();
    this.fillTable();
  }

  private fillTable(): void {
    const geneProfilesRequests = [];
    this.pageIndex = 1;
    this.loadMoreGenes = true;
    this.showNothingFound = false;
    // In case of page zoom out where scroll will disappear, load more pages.
    let initialPageCount = 0;
    if (this.viewportPageCount) {
      initialPageCount = 4 * this.viewportPageCount;
    }

    for (let i = 1; i <= initialPageCount; i++) {
      geneProfilesRequests.push(
        this.geneProfilesTableService
          .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
          .pipe(take(1))
      );
      this.pageIndex++;
    }
    this.pageIndex = initialPageCount;
    this.getGenesSubscription.unsubscribe();
    this.getGenesSubscription = zip(geneProfilesRequests).subscribe(res => {
      this.genes = [];
      for (const genes of res) {
        this.genes = this.genes.concat(genes);
      }
      this.updateShownGenes(0, this.viewportPageCount * this.config.pageSize);
      this.showNothingFound = !this.genes.length;
      this.showInitialLoading = false;
      this.showSearchLoading = false;
    });
  }

  private loadState(): void {
    this.store.selectOnce(
      (state: { geneProfilesState: GeneProfilesModel}) => state.geneProfilesState)
      .subscribe(state => {
        this.tabs = new Set(state.openedTabs);
        this.loadedSearchValue = state.searchValue;
        this.highlightedGenes = new Set(state.highlightedRows);
        this.orderBy = state.orderBy;
        this.leavesIds = state.headerLeaves;
        this.reorderHeaderByLeaves(this.config.columns);
        if (state.sortBy) {
          this.sortBy = state.sortBy;
        } else {
          this.setDefaultSortableCategory();
        }
        this.stateFinishedLoading = true;
        this.prepareTable();
      });

    this.search(this.loadedSearchValue);
  }

  private reorderHeaderByLeaves(
    columns: GeneProfilesColumn[],
  ): void {
    columns.sort((a, b) => {
      const aPosition = this.leavesIds.findIndex(l => l.startsWith(a.id));
      const bPosition = this.leavesIds.findIndex(l => l.startsWith(b.id));
      return aPosition - bPosition;
    });

    columns.forEach(column => this.reorderHeaderByLeaves(column.columns));
  }

  public setLeavesVisibility(): void {
    if (this.leavesIds.length) {
      this.leaves = GeneProfilesColumn.allLeaves(this.config.columns);
      this.leaves.map(leaf => {
        if (this.leavesIds.includes(leaf.id)) {
          leaf.visibility = true;
        } else {
          leaf.visibility = false;
        }
      });
    }
  }

  public resetLeavesIds(): void {
    this.leaves = GeneProfilesColumn.leaves(this.config.columns);
    this.leavesIds = [];
    this.leaves.map(leaf => {
      if (leaf.visibility) {
        this.leavesIds.push(leaf.id);
      }
    });
  }

  public calculateHeaderLayout(): void {
    this.resetLeavesIds();

    this.nothingFoundWidth = (this.leaves.length * 110) + 40; // must match .table-row values
    let columnIdx = 0;
    const maxDepth: number = Math.max(...this.leaves.map(leaf => leaf.depth));

    for (const leaf of this.leaves) {
      leaf.gridColumn = (columnIdx + 1).toString();
      GeneProfilesColumn.calculateGridRow(leaf, maxDepth);
      columnIdx++;
    }

    for (const column of this.config.columns) {
      GeneProfilesColumn.calculateGridColumn(column);
    }
    this.store.dispatch(new SetGeneProfilesHeader(this.leavesIds));
    this.geneProfilesTableService.saveUserGeneProfilesState();
  }

  public search(value: string): void {
    this.geneInput = value;
    this.store.dispatch(new SetGeneProfilesSearchValue(this.geneInput));
    this.geneProfilesTableService.saveUserGeneProfilesState();
    this.fillTable();
  }

  private updateShownGenes(fromRow: number, toRow: number): void {
    this.shownRows = [];
    for (let i = fromRow; i <= toRow; i++) {
      this.shownRows.push(i);
    }
  }

  public updateGenes(): void {
    this.pageIndex++;
    this.loadMoreGenes = false;
    this.geneProfilesTableService
      .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
      .pipe(take(1))
      .subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = Boolean(res.length); // stop making requests if the last response was empty
      });
  }

  public openDropdown(column: GeneProfilesColumn, $event: MouseEvent): void {
    $event.stopPropagation(); // stop propagation to avoid triggering sort

    if (this.ngbDropdownMenu.dropdown.isOpen()) {
      return;
    }

    this.ngbDropdownMenu.dropdown.toggle();
    this.clickedColumnFilteringButton = $event.target as HTMLElement;
    this.updateModalPosition();

    let columnDisplayName = column.displayName;
    if (column.depth !== 1) {
      columnDisplayName = columnDisplayName.slice(0, columnDisplayName.lastIndexOf('(') - 1);
    }
    this.multipleSelectMenuComponent.searchPlaceholder = `Search in "${columnDisplayName}"`;

    this.multipleSelectMenuComponent.columns = column.columns;
    this.multipleSelectMenuComponent.refresh();
  }

  public openCategoryFilterDropdown($event: MouseEvent): void {
    if (this.ngbDropdownMenu.dropdown.isOpen()) {
      return;
    }

    this.ngbDropdownMenu.dropdown.toggle();
    this.clickedColumnFilteringButton = $event.target as HTMLElement;
    this.updateModalPosition(0, -11);
    this.multipleSelectMenuComponent.searchPlaceholder = 'Search categories';
    this.multipleSelectMenuComponent.columns = this.config.columns.filter(col => col.id !== this.geneSymbolColumnId);
    this.multipleSelectMenuComponent.refresh();
  }

  public updateModalPosition(leftOffset = 6, topOffset = 0): void {
    if (!this.ngbDropdownMenu.dropdown.isOpen()) {
      return;
    }

    const buttonHeight = 30;
    this.modalPosition.top =
      this.clickedColumnFilteringButton.getBoundingClientRect().top
      + buttonHeight
      - topOffset;

    const modalWidth = 400;
    const leftPosition =
      this.clickedColumnFilteringButton.getBoundingClientRect().left
      + leftOffset;

    const viewWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const extraRightSpace = 48;

    if (leftPosition + modalWidth < viewWidth - extraRightSpace) {
      this.modalPosition.left = leftPosition;
    } else {
      this.modalPosition.left = viewWidth - modalWidth - extraRightSpace;
    }
  }

  public reorderHeader($event: string[]): void {
    this.config.columns.sort((a, b) => $event.indexOf(a.id) - $event.indexOf(b.id));
    this.calculateHeaderLayout();
  }

  public sort(sortBy: string, orderBy: string): void {
    if (this.sortBy !== sortBy) {
      this.resetSortButtons();
    }

    this.sortBy = sortBy;
    this.orderBy = orderBy;
    this.pageIndex = 1;

    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.emitSort();
    }
    this.fillTable();
    this.store.dispatch(new SetGeneProfilesOrderBy(this.orderBy));
    this.store.dispatch(new SetGeneProfilesSortBy(this.sortBy));
    this.geneProfilesTableService.saveUserGeneProfilesState();
  }

  private resetSortButtons(): void {
    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.resetSortState();
    }
  }

  public handleCellClick($event: MouseEvent, row: object, column: GeneProfilesColumn): void {
    const linkClick: boolean = ($event.target['classList'] as DOMTokenList).contains('clickable');
    const geneSymbol = row[this.geneSymbolColumnId] as string;

    const middleClick: boolean = $event.which === 2;
    const altAction: boolean = middleClick || $event.ctrlKey || $event.metaKey;

    if (!linkClick && altAction) {
      this.toggleHighlightGene(geneSymbol);
    } else if (column.clickable === 'goToQuery') {
      this.goToQueryEvent.emit({geneSymbol: geneSymbol, statisticId: column.id, newTab: altAction});
    } else if (column.clickable === 'createTab' && linkClick) {
      this.loadSingleView(geneSymbol, altAction);
    }
  }

  public loadSingleView(geneSymbols: string | Set<string>, newTab: boolean = false): void {
    const genes = this.formatGeneSymbols(geneSymbols);
    if (!newTab) {
      this.loadState();
      this.tabs.add(genes);
      this.store.dispatch(new SetGeneProfilesTabs([...this.tabs.values()]));
      this.geneProfilesTableService.saveUserGeneProfilesState();

      this.openTab(genes);
    } else {
      this.currentTabGeneSet.clear();
      this.currentTabGeneSet.add(genes);
      window.open(`${window.location.href}/${genes}`, '_blank');
    }
  }

  private formatGeneSymbols(geneSymbols: string | Set<string>): string {
    return typeof geneSymbols === 'string' ? geneSymbols : [...geneSymbols].sort().join(',');
  }

  public openTab(tab: string): void {
    this.hideTable = true;
    this.currentTabGeneSet.clear();
    tab.split(',').map(t => this.currentTabGeneSet.add(t));
    this.currentTabString = tab;
    this.location.replaceState('gene-profiles/' + this.currentTabString);
  }

  public closeTab(tab: string): void {
    this.tabs.delete(tab);
    this.store.dispatch(new SetGeneProfilesTabs([...this.tabs.values()]));
    this.geneProfilesTableService.saveUserGeneProfilesState();
    this.backToTable();
  }

  public backToTable(): void {
    this.hideTable = false;
    this.currentTabString = 'all genes';
    this.location.replaceState('gene-profiles');
  }

  public toggleHighlightGene(geneSymbol: string): void {
    if (this.highlightedGenes.has(geneSymbol)) {
      this.highlightedGenes.delete(geneSymbol);
    } else {
      this.highlightedGenes.add(geneSymbol);
    }
    this.store.dispatch(new SetGeneProfilesHighlightedRows([...this.highlightedGenes.values()]));
    this.geneProfilesTableService.saveUserGeneProfilesState();
  }

  private async waitForSearchBoxToLoad(): Promise<void> {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.searchBox !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 50);
    });
  }

  private focusSearchBox(): void {
    this.waitForSearchBoxToLoad().then(() => {
      (this.searchBox.nativeElement as HTMLInputElement).focus();
    });
  }

  public resetState(): void {
    this.tabs = new Set();
    this.highlightedGenes = new Set<string>();
    this.orderBy = 'desc';
    this.loadedSearchValue = '';
    (this.searchBox.nativeElement as HTMLInputElement).value = '';
    this.search(this.loadedSearchValue);
    this.setDefaultSortableCategory();

    this.resetConfig.emit();

    this.store.dispatch(new StateReset(GeneProfilesState));
    this.geneProfilesTableService.saveUserGeneProfilesState();
  }
}
