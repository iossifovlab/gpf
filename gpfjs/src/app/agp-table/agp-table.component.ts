
import { AfterViewInit, Component, ElementRef, HostListener, OnInit, QueryList, Renderer2, ViewChild, ViewChildren } from '@angular/core';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { ItemApplyEvent } from 'app/multiple-select-menu/multiple-select-menu';
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
export class AgpTableComponent implements OnInit {
  @ViewChildren('dropdownSpan') public dropdownSpans: QueryList<ElementRef>;
  @ViewChildren('columnFilteringButton') public columnFilteringButtons: QueryList<ElementRef>;
  @ViewChildren(SortingButtonsComponent) public sortingButtonsComponents: SortingButtonsComponent[];
  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild(MultipleSelectMenuComponent) public multipleSelectMenuComponent: MultipleSelectMenuComponent;

  public config: AgpConfig;
  public genes = [];

  public sortBy: string;
  public orderBy: string;
  public currentSortingColumnId: string;
  public modalBottom: number;
  public showSearchWarning = false;

  public geneInput: string;
  public searchKeystrokes$: Subject<string> = new Subject();

  private pageIndex = 1;

  private loadMoreGenes = true;
  private scrollLoadThreshold = 1000;
  public constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private renderer: Renderer2,
  ) { }

  @HostListener('window:scroll')
  public onWindowScroll(): void {
    const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
    const totalScrollHeight = document.documentElement.scrollHeight;

    if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
      this.updateGenes();
    }

    this.updateModalBottom();
  }

  public ngOnInit(): void {
    this.autismGeneProfilesService.getConfig().pipe(take(1)).subscribe(config => {
      this.config = config;

      this.sortBy = `autism_gene_sets_rank`;
      this.orderBy = 'desc';

      this.autismGeneProfilesService.getGenes(
        this.pageIndex, undefined, this.sortBy, this.orderBy
      ).pipe(take(1)).subscribe(res => {
        this.genes = this.genes.concat(res);
      });
    });

    this.searchKeystrokes$.pipe(
      debounceTime(250),
      distinctUntilChanged()
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });
  }

  public search(value: string): void {
    this.geneInput = value;
    this.genes = [];
    this.pageIndex = 0;

    this.updateGenes();
  }

  public sendKeystrokes(value: string): void {
    this.searchKeystrokes$.next(value);
  }

  public updateGenes(): void {
    this.loadMoreGenes = false;
    this.showSearchWarning = false;
    this.pageIndex++;

    this.autismGeneProfilesService
      .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
      .pipe(take(1))
      .subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = Object.keys(res).length !== 0;
        this.showSearchWarning = !this.loadMoreGenes;
      });
  }

  public createMultiSelectMenuSource(column: Column): { itemIds: string[]; shownItemIds: string[] } {
    const allNames = column.columns.map(col => col.displayName);
    const shownNames = column.columns.filter(col => col.visible).map(col => col.displayName);
    return { itemIds: allNames, shownItemIds: shownNames };
  }

  public openDropdown(column: Column): void {
    this.multipleSelectMenuComponent.menuId = column.id;
    this.multipleSelectMenuComponent.itemsSource = this.createMultiSelectMenuSource(column);

    this.waitForDropdown()
      .then(() => {
        this.ngbDropdownMenu.dropdown.open();
        this.multipleSelectMenuComponent.refresh();
      })
      .catch(err => console.error(err));
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

  public filterColumns($event: ItemApplyEvent): void {
    const menuId = $event.menuId.split('.');

    // Find column for filtering
    let column: Column = this.config.columns.find(col => col.id === menuId[0]);
    for (let i = 1; i < menuId.length; i++) {
      menuId[i] = `${ menuId[i-1] }.${ menuId[i] }`;
      column = column.columns.find(col => col.id === menuId[i]);
    }

    // Sort sub-columns according to the new order
    column.columns.sort((a, b) => $event.order.indexOf(a.displayName) - $event.order.indexOf(b.displayName));

    // Toggle sub-columns visibility according to the new selected
    let hiddenCounter = 0;
    column.columns.forEach(col => {
      if ($event.selected.indexOf(col.displayName) === -1) {
        col.visible = false;
        hiddenCounter++;
      }
      else {
        col.visible = true;
      }
    });

    // Toggle main column visibility if all sub-columns are hidden
    if (hiddenCounter === column.columns.length) {
      column.columns.forEach(col => {
        col.visible = true;
      });
      column.visible = false;
    }

    this.ngbDropdownMenu.dropdown.close();
  }

  public updateModalBottom(): void {
    const columnFilteringButton = this.columnFilteringButtons.first;
    let result = 0;

    if (columnFilteringButton) {
      result = window.innerHeight - columnFilteringButton.nativeElement.getBoundingClientRect().bottom;
      // If there is a horizontal scroll
      if (window.innerHeight !== document.documentElement.clientHeight) {
        result -= 15;
      }
    }
    this.modalBottom = result;
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

  public highlightRow(idx: number): void {
    const elements = document.getElementsByClassName(`row-${idx}`);
    for (let i = 0; i < elements.length; i++) {
      const backgroundColor = (elements[i] as HTMLElement).style.backgroundColor;
      if (!backgroundColor || backgroundColor === 'rgb(255, 255, 255)') {
        (elements[i] as HTMLElement).style.backgroundColor = 'rgb(237, 243, 255)';
      } else {
        (elements[i] as HTMLElement).style.backgroundColor = 'rgb(255, 255, 255)';
      }
    }
  }
}
