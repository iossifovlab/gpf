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

@Component({
  selector: 'gpf-gene-profiles-table',
  templateUrl: './gene-profiles-table.component.html',
  styleUrls: ['./gene-profiles-table.component.css']
})
export class GeneProfilesTableComponent implements OnInit, OnChanges, OnDestroy {
  @Input() public config: GeneProfilesTableConfig;
  @Input() public sortBy: string;
  public defaultSortBy: string;
  @Output() public goToQueryEvent = new EventEmitter();

  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild('dropdownSpan') public dropdownSpan: ElementRef;
  @ViewChild(MultipleSelectMenuComponent) public multipleSelectMenuComponent: MultipleSelectMenuComponent;
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];

  private clickedColumnFilteringButton;
  public modalPosition = {top: 0, left: 0};
  public showKeybinds = false;

  public leaves: GeneProfilesColumn[];
  public genes = [];
  public shownRows: number[] = []; // indexes
  public highlightedGenes: Set<string> = new Set();

  public geneSymbolColumnId = 'geneSymbol'; // must match the gene symbol column id from the backend

  public orderBy = 'desc';

  public geneInput: string = null;
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

  public tabs: string[] = [];
  public hideTable = false;
  public currentTab = new Set<string>();

  public constructor(
    private geneProfilesService: GeneProfilesTableService
  ) { }

  public ngOnInit(): void {
    this.defaultSortBy = this.sortBy;

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
  }

  public ngOnChanges(): void {
    if (this.config) {
      this.viewportPageCount = Math.ceil(window.innerHeight / (this.baseRowHeight * this.config.pageSize));
      this.calculateHeaderLayout();
      this.fillTable();
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
  public onWindowScroll($event): void {
    if (this.prevVerticalScroll !== $event.srcElement.scrollingElement.scrollTop) {
      const tableBodyOffset = document.getElementById('table-body').offsetTop;
      const topRowIdx = Math.floor(Math.max(window.scrollY - tableBodyOffset, 0) / this.baseRowHeight);
      const bottomRowIdx = Math.floor(window.innerHeight / this.baseRowHeight) + topRowIdx;
      this.prevVerticalScroll = $event.srcElement.scrollingElement.scrollTop;
      this.updateShownGenes(topRowIdx - 20, bottomRowIdx + 20);
      if (bottomRowIdx + 40 >= this.genes.length && this.loadMoreGenes) {
        this.updateGenes();
      }
    }

    const viewWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    if (window.scrollX + viewWidth < document.body.scrollWidth) {
      this.ngbDropdownMenu.dropdown.close();
    }
  }

  @HostListener('window:resize')
  public onResize(): void {
    this.ngbDropdownMenu.dropdown.close();
  }

  private fillTable(): void {
    const geneProfilesRequests = [];
    this.pageIndex = 1;
    this.loadMoreGenes = true;
    this.showNothingFound = false;
    // In case of page zoom out where scroll will disappear, load more pages.
    const initialPageCount = 4 * this.viewportPageCount;

    for (let i = 1; i <= initialPageCount; i++) {
      geneProfilesRequests.push(
        this.geneProfilesService
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

  public calculateHeaderLayout(): void {
    this.leaves = GeneProfilesColumn.leaves(this.config.columns);
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
  }

  public search(value: string): void {
    this.geneInput = value;
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
    this.geneProfilesService
      .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
      .pipe(take(1))
      .subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = Boolean(res.length); // stop making requests if the last response was empty
      });
  }

  public openDropdown(column: GeneProfilesColumn, $event): void {
    $event.stopPropagation(); // stop propagation to avoid triggering sort

    if (this.ngbDropdownMenu.dropdown._open) {
      return;
    }

    this.ngbDropdownMenu.dropdown.toggle();
    this.clickedColumnFilteringButton = $event.target;
    this.updateModalPosition();

    let columnDisplayName = column.displayName;
    if (column.depth !== 1) {
      columnDisplayName = columnDisplayName.slice(0, columnDisplayName.lastIndexOf('(') - 1);
    }
    this.multipleSelectMenuComponent.searchPlaceholder = `Search in "${columnDisplayName}"`;

    this.multipleSelectMenuComponent.columns = column.columns;
    this.multipleSelectMenuComponent.refresh();
  }

  public openCategoryFilterDropdown($event): void {
    if (this.ngbDropdownMenu.dropdown._open) {
      return;
    }

    this.ngbDropdownMenu.dropdown.toggle();
    this.clickedColumnFilteringButton = $event.target;
    this.updateModalPosition(0, -11);
    this.multipleSelectMenuComponent.searchPlaceholder = 'Search categories';
    this.multipleSelectMenuComponent.columns = this.config.columns.filter(col => col.id !== this.geneSymbolColumnId);
    this.multipleSelectMenuComponent.refresh();
  }

  public updateModalPosition(leftOffset = 6, topOffset = 0): void {
    if (!this.ngbDropdownMenu.dropdown._open) {
      return;
    }

    const buttonHeight = 30;
    this.modalPosition.top =
      (this.clickedColumnFilteringButton.getBoundingClientRect().top as number)
      + buttonHeight
      - topOffset;

    const modalWidth = 400;
    const leftPosition =
      (this.clickedColumnFilteringButton.getBoundingClientRect().left as number)
      + leftOffset;

    const viewWidth = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    const extraRightSpace = 48;

    if (leftPosition + modalWidth < viewWidth - extraRightSpace) {
      this.modalPosition.left = leftPosition;
    } else {
      this.modalPosition.left = viewWidth - modalWidth - extraRightSpace;
    }
  }

  public reorderHeader($event): void {
    this.config.columns.sort((a, b) => $event.indexOf(a.id) - $event.indexOf(b.id));
    this.calculateHeaderLayout();
  }

  public sort(sortBy: string, orderBy?: string): void {
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
  }

  private resetSortButtons(): void {
    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.resetSortState();
    }
  }

  public handleCellClick($event, row: object, column: GeneProfilesColumn): void {
    const linkClick: boolean = $event.target.classList.contains('clickable');
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
    let genes: string;
    const geneProfilesBaseUrl = window.location.href;

    if (typeof geneSymbols === 'string') {
      genes = geneSymbols;
      if (this.tabs.indexOf(geneSymbols) === -1) {
        this.tabs.push(genes);
      }
    } else {
      genes = [...geneSymbols].join(',');
      if (this.tabs.indexOf(genes) === -1) {
        this.tabs.push(genes);
      }
    }

    if (genes) {
      this.openTab(genes);
    }

    if (newTab) {
      const newWindow = window.open('', '_blank');
      newWindow.location.assign(`${geneProfilesBaseUrl}/${genes}`);
    }
  }

  public openTab(tab: string): void {
    this.hideTable = true;
    this.currentTab.clear();
    tab.split(',').map(t => this.currentTab.add(t));
  }

  public closeTab(tab: string): void {
    this.tabs = this.tabs.filter(t => t !== tab);
    this.hideTable = false;
  }

  public toggleHighlightGene(geneSymbol: string): void {
    if (this.highlightedGenes.has(geneSymbol)) {
      this.highlightedGenes.delete(geneSymbol);
    } else {
      this.highlightedGenes.add(geneSymbol);
    }
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
}
