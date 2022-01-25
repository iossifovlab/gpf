import { Component, EventEmitter, HostListener, Input, OnChanges, OnInit, Output, ViewChild, ViewChildren } from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { AgpConfig, Column } from './agp-table';
import { AutismGeneProfilesService } from 'app/agp-table/agp-table.service';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';
import { Subject } from 'rxjs';

@Component({
  selector: 'gpf-agp-table',
  templateUrl: './agp-table.component.html',
  styleUrls: ['./agp-table.component.css']
})
export class AgpTableComponent implements OnInit, OnChanges {
  @Input() public config: AgpConfig;
  @Output() public createTabEvent = new EventEmitter();

  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
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
    private autismGeneProfilesService: AutismGeneProfilesService,
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
  public clearHighlights() {
    this.clearHighlightedGenes();
  }

  @HostListener('window:scroll')
  public onWindowScroll(): void {
    // TODO Add optimization to infinite scroll
    // FIXME Doesn't autoload rows when there's no scrollbar initially
    const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
    const totalScrollHeight = document.documentElement.scrollHeight;
    if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
      this.updateGenes();
    }
  }

  public calculateHeaderLayout(): void {
    this.leaves = Column.leaves(this.config.columns);
    let columnIdx = 1;
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

  public openDropdown(column: Column): void {
    this.multipleSelectMenuComponent.menuId = column.id;
    this.multipleSelectMenuComponent.columns = column.columns;

    this.waitForDropdown().then(() => {
      if (this.ngbDropdownMenu.dropdown.isOpen()) {
        // FIXME This is never carried out
        this.ngbDropdownMenu.dropdown.close();
      } else {
        this.ngbDropdownMenu.dropdown.open();
        this.multipleSelectMenuComponent.refresh();
      }
    }).catch(err => console.error(err));
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

  public sort(sortBy: string, orderBy?: string): void {
    if (this.sortBy !== sortBy) {
      this.resetSortButtons();
    }

    this.sortBy = sortBy;
    this.orderBy = orderBy;
    this.pageIndex = 1;

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

  public goToPage(page: number): void {
    if (this.pageIndex === page || (this.pageIndex < 1 && this.pageIndex > 123123)) {
      return;
    }
    this.pageIndex = page;
    this.updateGenes();
  }

  public previousPage(): void {
    if (this.pageIndex > 1) {
      this.goToPage(this.pageIndex - 1);
    }
  }

  public nextPage(): void {
    // FIXME this should have a sensible value with some page count from the backend
    if (this.pageIndex < 123123) {
      this.goToPage(this.pageIndex + 1);
    }
  }

  get pageRange(): number[] {
    const result: number[] = [];
    for (let i = Math.max(this.pageIndex - 4, 1); i <= this.pageIndex + 4; i++) {
      result.push(i);
    }
    return result;
  }

  public clearHighlightedGenes(): void {
    for (const gene of this.highlightedGenes) {
      this.toggleHighlightGene(gene);
    }
  }

  public emitCreateTabEvent(geneSymbol: string = null, navigateToTab: boolean = true): void {
    // if ($event && $event.ctrlKey && $event.type === 'click') {
    //   navigateToTab = false;
    // }
    console.log(geneSymbol);
    const geneSymbols: string[] = geneSymbol ? [geneSymbol] : Array.from(this.highlightedGenes);
    this.createTabEvent.emit({geneSymbols: geneSymbols, navigateToTab: navigateToTab});
  }
}
