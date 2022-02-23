import { Component, ElementRef, EventEmitter, HostListener, Input, OnChanges, OnDestroy, OnInit, Output, ViewChild, ViewChildren } from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { debounceTime, distinctUntilChanged, take, tap } from 'rxjs/operators';
import { forkJoin, Subject, Subscription } from 'rxjs';
import { AgpTableConfig, Column } from './autism-gene-profiles-table';
import { AgpTableService } from './autism-gene-profiles-table.service';
import * as _ from 'lodash';

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css']
})
export class AgpTableComponent implements OnInit, OnChanges, OnDestroy {
  @Input() public config: AgpTableConfig;
  @Output() public createTabEvent = new EventEmitter();
  @Output() public goToQueryEvent = new EventEmitter();
  @Input() public isSingleViewVisible: boolean;

  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild('dropdownSpan') public dropdownSpan;
  @ViewChild(MultipleSelectMenuComponent) public multipleSelectMenuComponent: MultipleSelectMenuComponent;
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];

  private clickedColumnFilteringButton;
  public modalPosition = {top: 0, left: 0};
  public showKeybinds = false;

  public leaves: Column[];
  public genes = [];
  public shownRows: number[] = []; // indexes
  public highlightedGenes: Set<string> = new Set();

  public geneSymbolColumnId = "geneSymbol" // must match the gene symbol column id from the backend

  public sortBy = "autism_gene_sets_rank";
  public orderBy = "desc";

  public geneInput: string = null;
  public searchKeystrokes$: Subject<string> = new Subject();
  public pageIndex = 0;
  public showNothingFound = false;
  public showInitialLoading = true;
  public showSearchLoading;

  private viewportPageCount;
  private baseRowHeight = 35; // px, this should match the height found in the table-row CSS class
  private prevVerticalScroll = 0;
  private loadMoreGenes = true;
  private keystrokeSubscription: Subscription;

  public sortingHeaderId: string;

  public constructor(
    private autismGeneProfilesService: AgpTableService,
    private ref: ElementRef,
  ) { }

  public ngOnInit(): void {
    this.keystrokeSubscription = this.searchKeystrokes$.pipe(
      distinctUntilChanged(),
      tap(() => {
        this.showSearchLoading = true;
      })
    ).pipe(
      debounceTime(250)
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });
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
  public keybindClearHighlight() {
    if (this.isSingleViewVisible) {
      return;
    }

    if (this.highlightedGenes.size && document.activeElement === document.body) {
      this.highlightedGenes.clear();
    }
  }

  @HostListener('document:keydown.f')
  public keybindCompareGenes() {
    if (this.isSingleViewVisible) {
      return;
    }

    if (this.highlightedGenes.size && document.activeElement === document.body) {
      this.emitCreateTabEvent();
    }
  }

  @HostListener('window:scroll', ['$event'])
  public onWindowScroll($event): void {
    // execute this code only if the table is shown and the scroll event is a vertical scroll
    if (!this.ref.nativeElement.hidden && this.prevVerticalScroll !== $event.srcElement.scrollingElement.scrollTop) {
      const tableBodyOffset = document.getElementById('table-body').offsetTop;
      const topRowIdx = Math.floor(Math.max(window.scrollY - tableBodyOffset, 0) / this.baseRowHeight);
      const bottomRowIdx = Math.floor(window.innerHeight / this.baseRowHeight) + topRowIdx;
      this.prevVerticalScroll = $event.srcElement.scrollingElement.scrollTop;
      this.updateShownGenes(topRowIdx - 5, bottomRowIdx + 5);
      if (bottomRowIdx + 10 >= this.genes.length && this.loadMoreGenes) {
        this.updateGenes();
      }
    }
    this.ngbDropdownMenu.dropdown.close();
  }

  @HostListener('window:resize')
  public onResize() {
    this.ngbDropdownMenu.dropdown.close();
  }

  private fillTable() {
    const agpRequests = [];
    this.genes = [];
    this.pageIndex = 1;
    this.loadMoreGenes = true;
    this.showNothingFound = false;
    
    for (let i = 1; i <= this.viewportPageCount; i++) {
      agpRequests.push(
        this.autismGeneProfilesService
          .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
          .pipe(take(1))
      )
      this.pageIndex++;
    }
    this.pageIndex = this.viewportPageCount;
    forkJoin(agpRequests).subscribe(res => {
      for (const genes of res) {
        this.genes = this.genes.concat(genes);
      }
      this.updateShownGenes(0, this.viewportPageCount * this.config.pageSize);
      this.showNothingFound = !this.genes.length;
      this.showInitialLoading = false;
      this.showSearchLoading = false;
    })
  }

  public calculateHeaderLayout(): void {
    this.leaves = Column.leaves(this.config.columns);
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
    this.multipleSelectMenuComponent.columns = column.columns;
    this.multipleSelectMenuComponent.refresh();
  }

  public openCategoryFilterDropdown($event): void {
    if (this.ngbDropdownMenu.dropdown._open) {
      return;
    }

    this.ngbDropdownMenu.dropdown.toggle();
    this.clickedColumnFilteringButton = $event.target;
    this.updateModalPosition(1, -9);
    this.multipleSelectMenuComponent.columns = this.config.columns.filter(col => col.id !== this.geneSymbolColumnId);
    this.multipleSelectMenuComponent.refresh();
  }

  public updateModalPosition(leftOffset = 6, topOffset = 5): void {
    if (!this.ngbDropdownMenu.dropdown._open) {
      return;
    }

    const buttonHeight = 30;
    this.modalPosition.top = 
      this.clickedColumnFilteringButton.getBoundingClientRect().top
      + buttonHeight
      - topOffset;

    const leftCap = 17;
    const modalWidth = 400;
    const leftPosition =
      this.clickedColumnFilteringButton.getBoundingClientRect().right
      - modalWidth
      - leftOffset;

    if (leftPosition > leftCap) {
      this.modalPosition.left = leftPosition;
    } else {
      this.modalPosition.left = leftCap;
    }
  }

  public reorderHeader($event) {
    this.config.columns.sort((a, b) => $event.indexOf(a.id) - $event.indexOf(b.id));
    this.calculateHeaderLayout();
  }

  public sort(sortBy: string, orderBy?: string): void {
    if (this.sortBy !== sortBy) {
      this.sortingHeaderId = '';
      this.resetSortButtons();
    }

    this.sortBy = sortBy;
    this.orderBy = orderBy;
    this.pageIndex = 1;
    this.genes = [];
    this.sortingHeaderId = sortBy;

    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    sortButton.emitSort();
    this.fillTable();
  }

  public resetSortButtons(): void {
    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.resetHideState();
    }
  }

  public handleCellClick($event, row, column): void {
    if (column.clickable && row[column.id] && ($event.which === 2 || ($event.ctrlKey || $event.metaKey))) {
      this.emitClickEvent($event, row, column, false);
    } else if ($event.which === 2 || ($event.ctrlKey || $event.metaKey)) {
      this.toggleHighlightGene(row[this.geneSymbolColumnId])
    } else {
      this.emitClickEvent($event, row, column);
    }
  }

  public toggleHighlightGene(geneSymbol: string): void {
    if (this.highlightedGenes.has(geneSymbol)) {
      this.highlightedGenes.delete(geneSymbol);
    } else {
      this.highlightedGenes.add(geneSymbol);
    }
  }

  public emitClickEvent($event, row, column, navigateToTab: boolean = true): void {
    if (column.clickable === 'goToQuery' && row[column.id]) {
      this.goToQueryEvent.emit({geneSymbol: row[this.geneSymbolColumnId], statisticId: column.id});
    } else if (column.clickable === 'createTab') {
      if ($event.ctrlKey || $event.metaKey) {
        navigateToTab = false;
      }
      this.emitCreateTabEvent(null, row[this.geneSymbolColumnId], navigateToTab)
    }
  }

  public emitCreateTabEvent($event = null, geneSymbol: string = null, navigateToTab: boolean = true): void {
    if ($event && ($event.ctrlKey || $event.metaKey)) {
      navigateToTab = false;
    }

    if (navigateToTab) {
      /* navigating to another tab does not guarantee the scroll position
       * will remain the same, so we reset it and update the shownGenes indices */
      window.scrollTo(0, 0);
      this.updateShownGenes(0, this.viewportPageCount * this.config.pageSize);
    }

    const geneSymbols: string[] = geneSymbol ? [geneSymbol] : Array.from(this.highlightedGenes);
    this.createTabEvent.emit({geneSymbols: geneSymbols, navigateToTab: navigateToTab});
  }
}
