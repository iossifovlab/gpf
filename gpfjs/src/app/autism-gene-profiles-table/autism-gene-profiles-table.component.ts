import {
  AfterViewInit, ChangeDetectorRef, Component, ElementRef, EventEmitter, HostListener,
  Input, OnChanges, OnInit, Output, QueryList, Renderer2, ViewChild, ViewChildren
} from '@angular/core';
// tslint:disable-next-line:import-blacklist
import { Subject } from 'rxjs';
import { AgpTableConfig, AgpTableDataset, AgpGene, AgpGeneSetsCategory, AgpGenomicScoresCategory, AgpDatasetStatistic } from './autism-gene-profile-table';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { NgbDropdownMenu } from '@ng-bootstrap/ng-bootstrap';
import { SortingButtonsComponent } from 'app/sorting-buttons/sorting-buttons.component';
import { cloneDeep } from 'lodash';
import { sprintf } from 'sprintf-js';
import { QueryService } from 'app/query/query.service';
import { GenomicScore, PeopleGroup } from 'app/genotype-browser/genotype-browser';
import { EffectTypes } from 'app/effecttypes/effecttypes';
import { Store } from '@ngxs/store';
import { SetGeneSymbols } from 'app/gene-symbols/gene-symbols.state';
import { SetEffectTypes } from 'app/effecttypes/effecttypes.state';
import { SetStudyTypes } from 'app/study-types/study-types.state';
import { SetVariantTypes } from 'app/varianttypes/varianttypes.state';
import { SetGenomicScores } from 'app/genomic-scores-block/genomic-scores-block.state';
import { SetPresentInParentValues } from 'app/present-in-parent/present-in-parent.state';
import { SetPresentInChildValues } from 'app/present-in-child/present-in-child.state';
import { SetPedigreeSelector } from 'app/pedigree-selector/pedigree-selector.state';
import { debounceTime, distinctUntilChanged, take } from 'rxjs/operators';

@Component({
  selector: 'gpf-autism-gene-profiles-table',
  templateUrl: './autism-gene-profiles-table.component.html',
  styleUrls: ['./autism-gene-profiles-table.component.css'],
})
export class AutismGeneProfilesTableComponent implements OnInit, AfterViewInit, OnChanges {
  @Input() config: AgpTableConfig;
  @Output() configChange: EventEmitter<AgpTableConfig> = new EventEmitter<AgpTableConfig>();

  @Output() createTabEvent = new EventEmitter();
  @ViewChildren(NgbDropdownMenu) ngbDropdownMenu: NgbDropdownMenu[];

  private genes: AgpGene[] = [];

  public shownGeneSetsCategories: AgpGeneSetsCategory[];
  allGeneSetNames = new Map<string, string[]>();
  shownGeneSetNames = new Map<string, string[]>();

  public shownGenomicScoresCategories: AgpGenomicScoresCategory[];
  allGenomicScoresNames = new Map<string, string[]>();
  shownGenomicScoresNames = new Map<string, string[]>();

  public shownDatasets: AgpTableDataset[];
  allDatasetNames = new Map<string, Map<string, string[]>>();
  shownDatasetNames = new Map<string, Map<string, string[]>>();
  allPersonSetNames: string[] = [];
  shownPersonSetNames: string[] = [];

  private pageIndex = 1;
  private loadMoreGenes = true;
  private scrollLoadThreshold = 1000;

  // private focusGeneSetsInputs: boolean[];
  // private focusGenomicScoresInputs: boolean[];

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

  effectTypes = {
    lgds: EffectTypes['LGDS'],
    intron: ['Intron'],
    missense: ['Missense'],
  };

  @HostListener('window:scroll', ['$event'])
  onWindowScroll() {
    if (this.isTableVisible) {
      const currentScrollHeight = document.documentElement.scrollTop + document.documentElement.offsetHeight;
      const totalScrollHeight = document.documentElement.scrollHeight;

      if (this.loadMoreGenes && currentScrollHeight + this.scrollLoadThreshold >= totalScrollHeight) {
        this.updateGenes();
      }

      this.updateModalBottom();
    }
  }

  @HostListener('window:resize', ['$event'])
  onResize() {
    if (this.isTableVisible) {
      this.updateModalBottom();
    }
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
    private renderer: Renderer2,
    private cdr: ChangeDetectorRef,
    private ref: ElementRef,
    private queryService: QueryService,
    private store: Store,
  ) { }

  ngOnChanges(): void {
    this.shownGeneSetsCategories = this.mergeArrays(this.shownGeneSetsCategories, this.config.geneSets, 'category');
    this.shownGenomicScoresCategories = this.mergeArrays(this.shownGenomicScoresCategories, this.config.genomicScores, 'category');
    this.shownDatasets = this.mergeArrays(this.shownDatasets, cloneDeep(this.config.datasets), 'id');
  }

  /**
   * Merges objects from one array onto another, without updating already existing objects
   * @param oldArray array that needs to be updated
   * @param newArray array used to update the other
   * @param matchingProperty object property used to check if object already exists when adding it
   * @returns updated category array
   */
  mergeArrays(oldArray, newArray, matchingProperty) {
    return newArray.map(newObject => {
      if (oldArray) {
        const oldObject = oldArray.find(obj => newObject[matchingProperty] === obj[matchingProperty]);
        newObject = oldObject ? oldObject : newObject;
      }
      return newObject;
    });
  }

  /**
   * Initializes component. Prepares shown categories, genes, gene search field
   * and sets the first table column as current for sorting.
   */
  ngOnInit(): void {
    this.shownGeneSetsCategories = cloneDeep(this.config.geneSets);
    this.shownGenomicScoresCategories = cloneDeep(this.config.genomicScores);
    this.shownDatasets = cloneDeep(this.config.datasets);

    this.sortBy = `${this.shownGeneSetsCategories[0].category}_rank`;
    this.orderBy = 'desc';
    this.currentSortingColumnId = this.sortBy;
    this.autismGeneProfilesService.getGenes(
      this.pageIndex, undefined, this.sortBy, this.orderBy
    ).pipe(take(1)).subscribe(res => {
      this.genes = this.genes.concat(res);
    });

    this.searchKeystrokes$.pipe(
      debounceTime(250),
      distinctUntilChanged()
    ).subscribe(searchTerm => {
      this.search(searchTerm);
    });
  }

  /**
   * After component initialization - focuses gene search field,
   * initializes column filtering modals position update logic, updates first table column sorting buttons.
   */
  ngAfterViewInit(): void {
    this.focusGeneSearch();

    this.columnFilteringButtons.changes.pipe(take(1)).subscribe(() => {
      this.updateModalBottom();
      this.cdr.detectChanges();
    });

    const firstSortingButton = this.sortingButtonsComponents.find(sortingButtonsComponent => {
      return sortingButtonsComponent.id === `${this.shownGeneSetsCategories[0].category}_rank`;
    });
    firstSortingButton.hideState = 1;
  }

  get isTableVisible(): boolean {
    return !this.ref.nativeElement.hidden;
  }

  /**
   * Updates column filtering modals position value.
   */
  updateModalBottom() {
    this.modalBottom = this.calculateModalBottom();
  }

  /**
   * Calculates column filtering modals position.
   * @returns modals position
   */
  calculateModalBottom(): number {
    const columnFilteringButton = this.columnFilteringButtons.first;
    if (columnFilteringButton) {
      return window.innerHeight - columnFilteringButton.nativeElement.getBoundingClientRect().bottom;
    }
    return 0;
  }

  /**
   * Handles column filtering menu apply events. Updates shown columns to match the one in the event.
   * @param $event event containing menu id and filtered columns
   */
  handleMultipleSelectMenuApplyEvent($event) {
    const menuId = $event.menuId.split(':');
    if (menuId[0] === 'gene_set_category') {
      const categoryIndex = this.shownGeneSetsCategories.findIndex(category => category.category === menuId[1]);

      this.shownGeneSetsCategories[categoryIndex].sets = this.config.geneSets
        .find(category => category.category === menuId[1]).sets
        .filter(set => $event.data.includes(set.setId));

      if (this.shownGeneSetsCategories[categoryIndex].sets.length === 0) {
        this.config.geneSets.splice(categoryIndex, 1);
        this.shownGeneSetsCategories = this.mergeArrays(this.shownGeneSetsCategories, cloneDeep(this.config.geneSets), 'category');

        this.configChange.emit(this.config);
      }
    } else if (menuId[0] === 'genomic_scores_category') {
      const categoryIndex = this.shownGenomicScoresCategories.findIndex(category => category['category'] === menuId[1]);

      this.shownGenomicScoresCategories[categoryIndex].scores = this.config.genomicScores
        .find(category => category.category === menuId[1]).scores
        .filter(score => $event.data.includes(score.scoreName));

      if (this.shownGenomicScoresCategories[categoryIndex].scores.length === 0) {
        this.config.genomicScores.splice(categoryIndex, 1);
        this.shownGenomicScoresCategories = this.mergeArrays(this.shownGenomicScoresCategories, cloneDeep(this.config.genomicScores), 'category');

        this.configChange.emit(this.config);
      }
    } else if (menuId[0] === 'dataset') {
      const datasetIndex = this.shownDatasets.findIndex(dataset => dataset.id === menuId[1]);

      if (menuId.length === 2) {
        this.shownDatasets[datasetIndex].personSets = this.mergeArrays(
          this.shownDatasets[datasetIndex].personSets,
          cloneDeep(this.config.datasets[datasetIndex].personSets.filter(personSet => $event.data.includes(personSet.displayName))),
          'id'
        );
      } else {
        const currentPersonSetRef = this.shownDatasets[datasetIndex].personSets.find(personSet => personSet.id === menuId[2]);
        currentPersonSetRef.statistics = this.config.datasets[datasetIndex].personSets
          .find(personSet => personSet.id === menuId[2]).statistics
          .filter(statistic => $event.data.includes(statistic.displayName));

        if (currentPersonSetRef.statistics.length === 0) {
          this.shownDatasets[datasetIndex].personSets
            .splice(this.shownDatasets[datasetIndex].personSets.findIndex(personSet => personSet.id === menuId[2]), 1);
        }
      }
      if (this.shownDatasets[datasetIndex].personSets.length === 0) {
        this.config.datasets.splice(datasetIndex, 1);
        this.shownDatasets = this.mergeArrays(this.shownDatasets, cloneDeep(this.config.datasets), 'id');

        this.configChange.emit(this.config);
      }
    }

    this.ngbDropdownMenu.forEach(menu => menu.dropdown.close());
  }

  /**
   * Emits create tab event.
   * @param geneSymbol gene symbol specifying which gene tab needs to open/close
   * @param openTab condition specifying to open or close the tab
   */
  emitCreateTabEvent(geneSymbol: string, openTab: boolean): void {
    this.createTabEvent.emit({geneSymbol: geneSymbol, openTab: openTab});
  }

  /**
   * Updates genes. Can load the next set of genes, load only searched genes, load genes sorted and ordered by.
   */
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

  /**
   * Sets gene input to be searched, resets currently loaded genes and triggers genes update.
   * @param value value used to filter matching genes
   */
  search(value: string) {
    this.geneInput = value;
    this.genes = [];
    this.pageIndex = 0;

    this.updateGenes();
  }

  /**
   * Updates search value to the input value.
   * @param value input value
   */
  sendKeystrokes(value: string) {
    this.searchKeystrokes$.next(value);
  }

  /**
   * Waits gene search element to load.
   * @returns promise
   */
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

  /**
   * Waits gene search input element to load and focuses it.
   */
  focusGeneSearch() {
    this.waitForGeneSearchToLoad().then(() => {
      this.geneSearchInput.nativeElement.focus();
    });
  }

  /**
   * Sets genes sorting conditions, resets currently loaded genes and triggers genes update.
   * @param sortBy what column to sort by
   * @param orderBy in what order to sort by
   */
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

  /**
   * Resets sorting button on current sorting column.
   * @param sortBy the new current column
   */
  resetSortButtons(sortBy: string) {
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

  /**
   * Updates all and shown gene sets names in certain category.
   * @param geneSetCategory in what category to update the names
   */
  openGeneSetCategoryDropdown(geneSetCategory: AgpGeneSetsCategory) {
    this.allGeneSetNames.set(geneSetCategory.category, this.config.geneSets
      .find(category => geneSetCategory.displayName === category.displayName).sets
      .map(set => set.setId));
    this.shownGeneSetNames.set(geneSetCategory.category, geneSetCategory.sets
      .map(set => set.setId));

    this.openDropdown(geneSetCategory.category);
  }

  /**
   * Updates all and shown genomic scores names in certain category.
   * @param genomicScoresCategory in what category to update the names
   */
  openGenomicScoresCategoryDropdown(genomicScoresCategory: AgpGenomicScoresCategory) {
    this.allGenomicScoresNames.set(genomicScoresCategory.category, this.config.genomicScores
      .find(category => genomicScoresCategory.displayName === category.displayName).scores
      .map(score => score.scoreName));
    this.shownGenomicScoresNames.set(genomicScoresCategory.category, genomicScoresCategory.scores
      .map(score => score.scoreName));

    this.openDropdown(genomicScoresCategory.category);
  }

  openDatasetDropdown(dataset: AgpTableDataset, menuToOpen: string) {
    this.allDatasetNames.set(
      dataset.displayName,
      new Map(this.config.datasets.find(set => set.id === dataset.id).personSets.map(personSet =>
          [personSet.displayName, personSet.statistics.map(statistic => statistic.displayName)])
      )
    );
    this.allPersonSetNames = Array.from(this.allDatasetNames.get(dataset.displayName).keys());

    this.shownDatasetNames.set(
      dataset.displayName,
      new Map(dataset.personSets.map(personSet =>
          [personSet.displayName, personSet.statistics.map(statistic => statistic.displayName)])
      )
    );
    this.shownPersonSetNames = Array.from(this.shownDatasetNames.get(dataset.displayName).keys());

    this.openDropdown(menuToOpen);
  }

  /**
   * Waits dropdown to initialize.
   * @returns promise
   */
  async waitForDropdown() {
    if (this.ngbDropdownMenu !== undefined) {
      return;
    }

    return new Promise<void>(resolve => {
      const timer = setInterval(() => {
        if (this.ngbDropdownMenu !== undefined) {
          resolve();
          clearInterval(timer);
        }
      }, 15);
    });
  }

  /**
   * Opens column filtering dropdown.
   * @param columnId id specifying which dropdown to open
   */
  openDropdown(columnId: string) {
    const dropdownId = columnId + '-dropdown';

    this.waitForDropdown().then(() => {
      this.updateDropdownPosition(columnId);
      this.ngbDropdownMenu.find(ele => ele.nativeElement.id === dropdownId).dropdown.open();
    });
  }

  /**
   * Updates dropdown horizontal position.
   * @param id id specifying which dropdown to open
   */
  updateDropdownPosition(id: string) {
    this.renderer.setStyle(
      this.dropdownSpans.find(ele => ele.nativeElement.id === `${id}-span`).nativeElement,
      'left',
      this.calculateModalLeftPosition(this.columnFilteringButtons.find(ele => ele.nativeElement.id === `${id}-button`).nativeElement)
    );
  }

  /**
   * Calculates dropdown horizontal position.
   * @param columnFilteringButton column filtering button element
   * @returns position
   */
  calculateModalLeftPosition(columnFilteringButton: HTMLElement): string {
    const modalWidth = 400;
    const leftCap = 30;
    const modalLeft = (columnFilteringButton.getBoundingClientRect().right - modalWidth) - (document.body.getBoundingClientRect().left);

    return (modalLeft >= leftCap ? modalLeft : leftCap) + 'px';
  }

  /**
   * Calculates column size.
   * @param columnsCount number of columns
   * @returns size
   */
  calculateColumnSize(columnsCount: number): string {
    let result: number;
    const singleColumnSize = 80;

    if (columnsCount === 1) {
      result = 160;
    } else {
      result = columnsCount * singleColumnSize;
    }

    return result + 'px';
  }

  /**
   * Extracts gene score value from certain score in category
   * @param gene gene containing the score
   * @param scoreCategory score category
   * @param scoreName score name
   * @returns gene score value
   */
  getGeneScoreValue(gene: AgpGene, scoreCategory: string, scoreId: string) {
    const genomicScore = gene.genomicScores
      .find(score => score.id === scoreCategory).scores
      .find(score => score.id === scoreId);

    return Number(sprintf(genomicScore.format, genomicScore.value)).toString();
  }

  getEffectTypeValue(gene, datasetId, personSetId, statisticId) {
    return gene.studies.find(study => study.id === datasetId)
      .personSets.find(personSet => personSet.id === personSetId)
      .effectTypes.find(effectType => effectType.id === statisticId)
      .value;
  }


  calculateDatasetColspan(dataset: AgpTableDataset) {
    let count = 0;
    dataset.personSets.forEach(personSet => count += personSet.statistics.length);
    return count;
  }

  goToQuery(geneSymbol: string, personSetId: string, datasetId: string, statistic: AgpDatasetStatistic) {
    const newWindow = window.open('', '_blank');

    const genomicScores: GenomicScore[] = [];
    if (statistic.scores) {
      genomicScores[0] = new GenomicScore(
        statistic.scores[0]['name'],
        statistic.scores[0]['min'],
        statistic.scores[0]['max'],
      );
    }

    const presentInChildValues = ['proband only', 'proband and sibling', 'sibling only'];
    const presentInParentRareValues = ['father only', 'mother only', 'mother and father'];

    let presentInParent: string[] = ['neither'];
    let rarityType = 'all';
    if (statistic.category === 'rare') {
      rarityType = 'rare';
      presentInParent = presentInParentRareValues;
    }

    this.store.dispatch([
      new SetGeneSymbols([geneSymbol]),
      new SetEffectTypes(new Set(this.effectTypes[statistic['effects'][0]])),
      new SetStudyTypes(new Set(['we'])),
      new SetVariantTypes(new Set(statistic['variantTypes'])),
      new SetGenomicScores(genomicScores),
      new SetPresentInChildValues(new Set(presentInChildValues)),
      new SetPresentInParentValues(new Set(presentInParent), rarityType, 0, 1),
      new SetPedigreeSelector('phenotype', new Set([personSetId])),
    ]);

    this.store.selectOnce(state => state).subscribe(state => {
      state['datasetId'] = datasetId;
      this.queryService.saveQuery(state, 'genotype')
      .pipe(take(1))
      .subscribe(urlObject => {
        const url = this.queryService.getLoadUrlFromResponse(urlObject);
        newWindow.location.assign(url);
      });
    });
  }
}
