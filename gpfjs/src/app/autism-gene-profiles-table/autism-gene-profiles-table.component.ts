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

  public pageIndex = 0;
  private loadMoreGenes = true;
  private scrollLoadThreshold = 500;

  public constructor(
    private autismGeneProfilesService: AgpTableService,
    private ref: ElementRef,
    private renderer: Renderer2,
  ) { }

  public ngOnInit(): void {
    this.updateGenes();
    
    this.searchKeystrokes$.pipe(
      debounceTime(250),
      distinctUntilChanged()
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });
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
    // TODO Add optimization to infinite scroll
    // FIXME Doesn't autoload rows when there's no scrollbar initially
    if (!this.ref.nativeElement.hidden) {
      const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
      const totalScrollHeight = document.documentElement.scrollHeight;
      if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
        this.updateGenes();
      }
    }
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
      });
  }

  public openDropdown(column: Column, $event): void {
    this.multipleSelectMenuComponent.columns = column.columns;
    this.ngbDropdownMenu.dropdown.open();
    this.multipleSelectMenuComponent.refresh();

    // calculate modal position
    let modalLeft = $event.target.getBoundingClientRect().left - document.body.getBoundingClientRect().left;
    const modalTop = $event.target.getBoundingClientRect().bottom;
    const dropdownMenuWidth = 400;

    if (modalLeft + dropdownMenuWidth > window.innerWidth) {
      modalLeft -= (modalLeft + dropdownMenuWidth - window.innerWidth);
    }

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
