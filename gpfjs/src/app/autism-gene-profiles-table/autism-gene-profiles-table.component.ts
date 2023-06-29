import {
  Component, ElementRef, EventEmitter, HostListener, Input, OnChanges,
  OnDestroy, OnInit, Output, ViewChild, ViewChildren
} from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { debounceTime, distinctUntilChanged, take, tap } from 'rxjs/operators';
import { Subject, Subscription, zip } from 'rxjs';
import { AgpTableConfig, Column } from './autism-gene-profiles-table';
import { AgpTableService } from './autism-gene-profiles-table.service';
import { environment } from 'environments/environment';

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css']
})
export class AgpTableComponent implements OnInit, OnChanges, OnDestroy {
  @Input() public config: AgpTableConfig;
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

  public leaves: Column[];
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

  public constructor(
    private autismGeneProfilesService: AgpTableService
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
      this.openSingleView(this.highlightedGenes);
    }
  }

  @HostListener('window:scroll', ['$event'])
  public onWindowScroll($event): void {
    if (this.prevVerticalScroll !== $event.srcElement.scrollingElement.scrollTop) {
      const tableBodyOffset = document.getElementById('table-body').offsetTop;
      const topRowIdx = Math.floor(Math.max(window.scrollY - tableBodyOffset, 0) / this.baseRowHeight);
      const bottomRowIdx = Math.floor(window.innerHeight / this.baseRowHeight) + topRowIdx;
      this.prevVerticalScroll = $event.srcElement.scrollingElement.scrollTop;
      this.updateShownGenes(topRowIdx - 5, bottomRowIdx + 5);
      if (bottomRowIdx + 10 >= this.genes.length && this.loadMoreGenes) {
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
    const agpRequests = [];
    this.pageIndex = 1;
    this.loadMoreGenes = true;
    this.showNothingFound = false;

    for (let i = 1; i <= this.viewportPageCount; i++) {
      agpRequests.push(
        this.autismGeneProfilesService
          .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
          .pipe(take(1))
      );
      this.pageIndex++;
    }
    this.pageIndex = this.viewportPageCount;
    this.getGenesSubscription.unsubscribe();
    this.getGenesSubscription = zip(agpRequests).subscribe(res => {
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
    this.leaves = Column.leaves(this.config.columns);
    this.nothingFoundWidth = (this.leaves.length * 110) + 40; // must match .table-row values
    let columnIdx = 0;
    const maxDepth: number = Math.max(...this.leaves.map(leaf => leaf.depth));

    for (const leaf of this.leaves) {
      leaf.gridColumn = (columnIdx + 1).toString();
      Column.calculateGridRow(leaf, maxDepth);
      columnIdx++;
    }

    for (const column of this.config.columns) {
      Column.calculateGridColumn(column);
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
    this.autismGeneProfilesService
      .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
      .pipe(take(1))
      .subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = Boolean(res.length); // stop making requests if the last response was empty
      });
  }

  public openDropdown(column: Column, $event): void {
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
      sortButton.resetHideState();
    }
  }

  public handleCellClick($event, row, column: Column): void {
    const linkClick: boolean = $event.target.classList.contains('clickable');
    const geneSymbol = row[this.geneSymbolColumnId] as string;

    if (!linkClick) {
      if ($event.which === 2 || ($event.ctrlKey || $event.metaKey)) {
        this.toggleHighlightGene(geneSymbol);
      }
    } else if (column.clickable === 'goToQuery') {
      this.goToQueryEvent.emit({geneSymbol, statisticId: column.id});
    } else if (column.clickable === 'createTab' && linkClick) {
      this.openSingleView(geneSymbol);
    }
  }

  public openSingleView(geneSymbols: string | Set<string>): void {
    const agpBaseUrl = window.location.href;
    let genes: string;

    if (typeof geneSymbols === 'string') {
      genes = geneSymbols;
    } else {
      genes = [...geneSymbols].join(',');
    }

    const newWindow = window.open('', '_blank');
    if (newWindow) {
      newWindow.location.assign(`${agpBaseUrl}/${genes}`);
    }
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
      this.searchBox.nativeElement.focus();
    });
  }
}
