import { Component, ElementRef, EventEmitter, HostListener, Input, OnChanges, OnInit, Output, Renderer2, ViewChild, ViewChildren } from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';
import { Subject } from 'rxjs';
import { AgpTableConfig, Column } from './autism-gene-profiles-table';
import { AgpTableService } from './autism-gene-profiles-table.service';

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css']
})
export class AgpTableComponent implements OnInit, OnChanges {
  @Input() public config: AgpTableConfig;
  @Output() public createTabEvent = new EventEmitter();
  @Output() public goToQueryEvent = new EventEmitter();

  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild('dropdownSpan') public dropdownSpan;
  @ViewChild(MultipleSelectMenuComponent) public multipleSelectMenuComponent: MultipleSelectMenuComponent;
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];

  public leaves: Column[];
  public genes = [];
  public highlightedGenes: Set<string> = new Set();

  public geneSymbolColumnId = "geneSymbol"

  public sortBy = "autism_gene_sets_rank";
  public orderBy = "desc";

  public geneInput: string = null;
  public searchKeystrokes$: Subject<string> = new Subject();

  private baseRowHeight = 35; // px, this should match the height found in the table-row CSS class
  private actualRowHeight: number; // row height as it appears on screen, accounting for zoom level

  public pageIndex = 0;
  private loadMoreGenes = true;
  private scrollLoadThreshold = 500;

  public constructor(
    private autismGeneProfilesService: AgpTableService,
    private ref: ElementRef,
    private renderer: Renderer2,
  ) { }

  public ngOnInit(): void {
    this.calculateActualRowHeight();
    const pagesToLoad = Math.ceil(window.innerHeight / (this.baseRowHeight * this.config.pageSize));
    for (let i = 0; i < pagesToLoad; i++) {
      this.updateGenes();
    }
    
    this.searchKeystrokes$.pipe(
      debounceTime(250),
      distinctUntilChanged()
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    })
  }

  public ngOnChanges(): void {
    if (this.config) {
      this.calculateHeaderLayout();
    }
  }

  @HostListener('document:keydown.esc')
  public keybindClearHighlight() {
    this.clearHighlightedGenes();
  }

  @HostListener('document:keydown.f')
  public keybindCompareGenes() {
    if(this.highlightedGenes.size > 0 && (document.activeElement === document.body)) {
      this.emitCreateTabEvent();
    }
  }

  @HostListener('window:resize')
  public onWindowResize(): void {
    this.calculateActualRowHeight();
  }

  @HostListener('window:scroll')
  public onWindowScroll(): void {
    if (!this.ref.nativeElement.hidden) {
      const tableBodyOffset = document.getElementById('table-body').offsetTop;
      const topRowIdx = Math.floor(Math.max(window.scrollY - tableBodyOffset, 0) / this.baseRowHeight);
      const bottomRowIdx = Math.floor(window.innerHeight / this.baseRowHeight) + topRowIdx;
      console.log(topRowIdx, bottomRowIdx);

      if (topRowIdx % this.config.pageSize > 1) {
        this.genes = this.genes.slice(topRowIdx - 10);
      }

      if (this.genes.length - bottomRowIdx <= this.config.pageSize) {
        this.updateGenes();
      }
    }
  }

  private calculateActualRowHeight() {
    const roundedZoomLevel = Math.round((window.devicePixelRatio + Number.EPSILON) * 100) / 100
    this.actualRowHeight = Math.round(((this.baseRowHeight * roundedZoomLevel) + Number.EPSILON) * 100) / 100
    console.log(this.actualRowHeight);
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
    this.genes = [];
    this.pageIndex = 0;
    this.updateGenes();
  }

  public updateGenes(): void {
    this.pageIndex++;
    this.loadMoreGenes = false;
    this.autismGeneProfilesService
      .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
      .pipe(take(1))
      .subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = true;
        document.getElementById('scroll-padder-bottom').style.height = `${(this.config.pageCount - this.pageIndex) * this.config.pageSize * this.actualRowHeight}px`;
        // document.getElementById('scroll-padder-top').style.height = `${this.pageIndex * this.config.pageSize * this.actualRowHeight}px`;
      });
  }

  public openDropdown(column: Column, $event): void {
    if (this.ngbDropdownMenu.dropdown._open) {
      return;
    }

    this.ngbDropdownMenu.dropdown.toggle();

    this.multipleSelectMenuComponent.columns = column.columns;
    this.multipleSelectMenuComponent.refresh();

    // calculate modal position
    const dropdownMenuWidth = 400;
    const extraPaddingLeft = 8;
    const extraPaddingBottom = 6;

    const modalLeft = $event.target.getBoundingClientRect().right
      - dropdownMenuWidth
      - document.body.getBoundingClientRect().left
      - extraPaddingLeft;
    const modalTop = $event.target.getBoundingClientRect().bottom - extraPaddingBottom;

    this.renderer.setStyle(this.dropdownSpan.nativeElement, 'left', modalLeft + 'px');
    this.renderer.setStyle(this.dropdownSpan.nativeElement, 'top',  modalTop + 'px');
  }

  public sort(sortBy: string, orderBy?: string): void {
    if (this.sortBy !== sortBy) {
      this.resetSortButtons();
    }

    this.sortBy = sortBy;
    this.orderBy = orderBy;
    this.pageIndex = 1;
    this.genes = [];

    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    sortButton.emitSort();

    this.updateGenes();
  }

  public resetSortButtons(): void {
    const sortButton = this.sortingButtonsComponents.find(
      sortingButtonsComponent => sortingButtonsComponent.id === this.sortBy
    );

    if (sortButton) {
      sortButton.resetHideState();
    }
  }

  public toggleHighlightGene(geneSymbol: string): void {
    if (this.highlightedGenes.has(geneSymbol)) {
      this.highlightedGenes.delete(geneSymbol);
    } else {
      this.highlightedGenes.add(geneSymbol);
    }
  }

  public clearHighlightedGenes(): void {
    for (const gene of this.highlightedGenes) {
      this.toggleHighlightGene(gene);
    }
  }

  public emitClickEvent($event, row, column, navigateToTab: boolean = true) {
    if (column.clickable === 'goToQuery' && row[column.id]) {
      this.goToQueryEvent.emit({geneSymbol: row[this.geneSymbolColumnId], statisticId: column.id});
    } else if (column.clickable === 'createTab') {
      if ($event.ctrlKey) {
        navigateToTab = false;
      }
      this.emitCreateTabEvent(row[this.geneSymbolColumnId], navigateToTab)
    }
  }

  public emitCreateTabEvent(geneSymbol: string = null, navigateToTab: boolean = true): void {
    const geneSymbols: string[] = geneSymbol ? [geneSymbol] : Array.from(this.highlightedGenes);
    this.createTabEvent.emit({geneSymbols: geneSymbols, navigateToTab: navigateToTab});
  }
}
