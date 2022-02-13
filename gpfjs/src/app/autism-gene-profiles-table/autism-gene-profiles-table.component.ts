import { Component, ElementRef, EventEmitter, HostListener, Input, OnChanges, OnInit, Output, Renderer2, ViewChild, ViewChildren } from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';
import { forkJoin, Subject } from 'rxjs';
import { AgpTableConfig, Column } from './autism-gene-profiles-table';
import { AgpTableService } from './autism-gene-profiles-table.service';
import * as _ from 'lodash';

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
  public shownRows: number[] = []; // indexes
  public highlightedGenes: Set<string> = new Set();

  public geneSymbolColumnId = "geneSymbol"

  public sortBy = "autism_gene_sets_rank";
  public orderBy = "desc";

  public geneInput: string = null;
  public searchKeystrokes$: Subject<string> = new Subject();

  private baseRowHeight = 35; // px, this should match the height found in the table-row CSS class

  public pageIndex = 0;
  private loadMoreGenes = true;

  public constructor(
    private autismGeneProfilesService: AgpTableService,
    private ref: ElementRef,
    private renderer: Renderer2,
  ) { }

  public ngOnInit(): void {
    this.fillTable();
    
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

  @HostListener('window:scroll')
  public onWindowScroll(): void {
    if (!this.ref.nativeElement.hidden) {
      const tableBodyOffset = document.getElementById('table-body').offsetTop;
      const topRowIdx = Math.floor(Math.max(window.scrollY - tableBodyOffset, 0) / this.baseRowHeight);
      const bottomRowIdx = Math.floor(window.innerHeight / this.baseRowHeight) + topRowIdx;
      this.updateShownGenes(topRowIdx - 5, bottomRowIdx + 5);
    }
  }

  private fillTable() {
    const viewportPageCount = Math.ceil(window.innerHeight / (this.baseRowHeight * this.config.pageSize));
    const agpRequests = [];
    this.genes = [];
    
    for (let i = 1; i <= viewportPageCount; i++) {
      agpRequests.push(
        this.autismGeneProfilesService
          .getGenes(i, this.geneInput, this.sortBy, this.orderBy)
          .pipe(take(1))
      )
    }
    this.pageIndex = viewportPageCount;
    forkJoin(agpRequests).subscribe(res => {
      for (const genes of res) {
        this.genes = this.genes.concat(genes);
      }
      this.updateShownGenes(0, viewportPageCount * this.config.pageSize);
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
    this.genes = [];
    this.pageIndex = 0;
    this.fillTable();
  }

  private updateShownGenes(fromRow: number, toRow: number): void {
    this.shownRows = [];
    for (let i = fromRow; i <= toRow; i++) {
      this.shownRows.push(i);
    }
    if (toRow + 10 >= this.genes.length && this.loadMoreGenes) {
      this.loadMoreGenes = false;
      this.updateGenes();
    }
  }

  public updateGenes(): void {
    this.pageIndex++;
    this.autismGeneProfilesService
      .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
      .pipe(take(1))
      .subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = true;
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
