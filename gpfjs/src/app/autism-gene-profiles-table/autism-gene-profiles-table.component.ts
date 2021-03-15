import {
  AfterViewInit, ChangeDetectorRef, Component, ElementRef, EventEmitter, HostListener,
  Input, OnInit, Output, QueryList, Renderer2, ViewChild, ViewChildren
} from '@angular/core';
import { Subject } from 'rxjs';
import { AutismGeneToolConfig, AutismGeneToolGene } from './autism-gene-profile-table';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css'],
})
export class AutismGeneProfilesTableComponent implements OnInit, AfterViewInit {
  @Input() config: AutismGeneToolConfig;
  @Output() createTabEvent = new EventEmitter();
  @ViewChildren(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu[];

  private genes: AutismGeneToolGene[] = [];
  private shownGeneSets: string[];
  private shownAutismScores: string[];
  private shownProtectionScores: string[];

  private pageIndex = 1;
  private loadMoreGenes = true;
  private scrollLoadThreshold = 1000;

  private focusGeneSetsInput: boolean;
  private focusAutismScoresInput: boolean;
  private focusProtectionScoresInput: boolean;

  geneInput: string;
  searchKeystrokes$: Subject<string> = new Subject();
  @ViewChild('geneSearchInput') geneSearchInput: ElementRef;

  sortBy: string;
  orderBy: string;
  @ViewChildren(SortingButtonsComponent) sortingButtonsComponents: SortingButtonsComponent[];
  currentSortingColumnId: string;

  @ViewChildren('columnFilteringButton') columnFilteringButtons: QueryList<ElementRef>;
  @ViewChildren('dropdownSpan') dropdownSpans: QueryList<ElementRef>;
  modalBottom: number;

  @HostListener('window:scroll', ['$event'])
  onWindowScroll() {
    const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
    const totalScrollHeight = document.documentElement.scrollHeight;

    if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
      this.updateGenes();
    }

    this.modalBottom = this.calculateModalBottom();
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private renderer: Renderer2,
    private cdr: ChangeDetectorRef,
  ) { }

  ngOnInit(): void {
    this.shownGeneSets = this.config['geneSets'];
    this.shownAutismScores = this.config['autismScores'];
    this.shownProtectionScores = this.config['protectionScores'];

    this.autismGeneProfilesService.getGenes(this.pageIndex).take(1).subscribe(res => {
      this.genes = this.genes.concat(res);
    });

    this.searchKeystrokes$
      .debounceTime(250)
      .distinctUntilChanged()
      .subscribe(searchTerm => {
        this.search(searchTerm);
      });
  }

  ngAfterViewInit(): void {
    this.focusGeneSearch();

    this.columnFilteringButtons.changes.take(1).subscribe(() => {
      this.modalBottom = this.calculateModalBottom();
      this.cdr.detectChanges();
    });
  }

  calculateModalBottom(): number {
    return  window.innerHeight - this.columnFilteringButtons.first.nativeElement.getBoundingClientRect().bottom;
  }

  calculateDatasetColspan(datasetConfig) {
    return datasetConfig.effects.length * datasetConfig.personSets.length;
  }

  getMapValues(map: Map<string, number>) {
    return Array.from(map.values());
  }

  handleMultipleSelectMenuApplyEvent($event) {
    if ($event.id === 'geneSets') {
      this.shownGeneSets = $event.data;
    } else if ($event.id === 'autismScores') {
      this.shownAutismScores = $event.data;
    } else if ($event.id === 'protectionScores') {
      this.shownProtectionScores = $event.data;
    }

    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  emitCreateTabEvent(geneSymbol: string, openTab: boolean): void {
    this.createTabEvent.emit({geneSymbol: geneSymbol, openTab: openTab});
  }

  updateGenes() {
    this.loadMoreGenes = false;
    this.pageIndex++;

    this.autismGeneProfilesService
    .getGenes(this.pageIndex, this.geneInput, this.sortBy, this.orderBy)
    .take(1).subscribe(res => {
        this.genes = this.genes.concat(res);
        this.loadMoreGenes = Object.keys(res).length !== 0 ? true : false;
    });
  }

  search(value: string) {
    this.geneInput = value;
    this.genes = [];
    this.pageIndex = 0;

    this.updateGenes();
  }

  sendKeystrokes(value: string) {
    this.searchKeystrokes$.next(value);
  }

  async waitForGeneSearchToLoad() {
    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.geneSearchInput !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 100);
    });
  }

  focusGeneSearch() {
    this.waitForGeneSearchToLoad().then(() => {
      this.geneSearchInput.nativeElement.focus();
    });
  }

  sort(sortBy: string, orderBy?: string) {
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

  resetSortButtons(sortBy: string) {
    if (this.currentSortingColumnId !== undefined) {
      this.sortingButtonsComponents.find(
        sortingButtonsComponent => sortingButtonsComponent.id === this.currentSortingColumnId
      ).resetHideState();
    } 
    this.currentSortingColumnId = sortBy;
  }

  openDropdown(columnId: string) {
    const dropdownId = columnId + '-dropdown';

    this.updateDropdownPosition(columnId);
    this.ngbDropdownMenu.find(ele => ele.nativeElement.id === dropdownId).dropdown.open();
  }

  updateDropdownPosition(id: string) {
    this.renderer.setStyle(
      this.dropdownSpans.find(ele => ele.nativeElement.id === `${id}-span`).nativeElement,
      'left',
      this.calculateModalLeftPosition(this.columnFilteringButtons.find(ele => ele.nativeElement.id === `${id}-button`).nativeElement)
    );
  }

  calculateModalLeftPosition(columnFilteringButton: HTMLElement): string {
    const modalWidth = 400;
    return ((columnFilteringButton.getBoundingClientRect().right - modalWidth) - (document.body.getBoundingClientRect().left)) + 'px';
  }

  calculateColumnSize(columnsCount: number): string {
    let result: number;
    const singleColumnSize = 80;

    if (columnsCount === 1) {
      result = 200;
    } else {
      result = columnsCount * singleColumnSize;
    }

    return result + 'px';
  }
}
