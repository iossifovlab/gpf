import { Component, HostListener, OnInit, ViewChild } from '@angular/core';
import { NgbDropdownMenu, NgbNav } from '@ng-bootstrap/ng-bootstrap';
import {
  AgpConfig, AgpTableConfig,
  AgpTableDataset, AgpTableDatasetPersonSet
} from 'app/autism-gene-profiles-table/autism-gene-profile-table';
import { AutismGeneProfilesService } from 'app/autism-gene-profiles-block/autism-gene-profiles.service';
import { cloneDeep } from 'lodash';
import { take } from 'rxjs/operators';
import { MultipleSelectMenuComponent } from 'app/multiple-select-menu/multiple-select-menu.component';

@Component({
  selector: 'gpf-autism-gene-profiles-block',
  templateUrl: './autism-gene-profiles-block.component.html',
  styleUrls: ['./autism-gene-profiles-block.component.css']
})
export class AutismGeneProfilesBlockComponent implements OnInit {
  @ViewChild('nav') public nav: NgbNav;
  @ViewChild(NgbDropdownMenu) public ngbDropdownMenu: NgbDropdownMenu;
  @ViewChild(MultipleSelectMenuComponent) public multipleSelectMenuComponent: MultipleSelectMenuComponent;

  public geneTabs = new Set<string>();
  public autismGeneToolConfig: AgpConfig;
  public tableConfig: AgpTableConfig;
  public shownTableConfig: AgpTableConfig;

  public allColumns: string[];
  public shownColumns: string[];

  public showKeybinds = false;

  @HostListener('window:keydown', ['$event'])
  public keyEvent($event: KeyboardEvent) {
    if ($event.target['localName'] === 'input') {
      return;
    }

    const key = $event.key;

    if (key === 'w') {
      this.closeActiveTab();
    } else if (
        Number(key)
        || key === '0'
        || key === 'p'
        || key === 'n'
      ) {
      this.openTabByKey($event.key);
    }
  }

  constructor(
    private autismGeneProfilesService: AutismGeneProfilesService,
  ) { }

  public ngOnInit(): void {
    this.autismGeneProfilesService.getConfig().pipe(take(1)).subscribe(config => {
      this.autismGeneToolConfig = config;
      this.tableConfig = this.getTableConfig(config);
      this.shownTableConfig = cloneDeep(this.getTableConfig(config));

      this.shownTableConfig.geneSets = this.shownTableConfig.geneSets
      .filter(geneSet => geneSet.defaultVisible === true);
      this.shownTableConfig.genomicScores = this.shownTableConfig.genomicScores
      .filter(genomicScore => genomicScore.defaultVisible === true);
      this.shownTableConfig.datasets = this.shownTableConfig.datasets
      .filter(dataset => dataset.defaultVisible === true);

      this.allColumns = this.getAllCategories(this.tableConfig);
      this.shownColumns = this.getAllCategories(this.shownTableConfig);
    });
  }

  public createTabEventHandler($event): void {
    const tabId: string = $event.geneSymbol;
    const openTab: boolean = $event.openTab;

    this.geneTabs.add(tabId);
    if (openTab) {
      this.nav.select(tabId);
    }
  }

  public getActiveTabIndex(): number {
    return [...this.geneTabs].indexOf(this.nav.activeId);
  }

  public openHomeTab(): void {
    this.nav.select('autismGenesTool');
  }

  public openPreviousTab(): void {
    const index = this.getActiveTabIndex();

    if (index > 0) {
      this.openTabAtIndex(index - 1);
    } else {
      this.openHomeTab();
    }
  }

  public openNextTab(): void {
    const index = this.getActiveTabIndex();

    if (index + 1 < this.geneTabs.size) {
      this.openTabAtIndex(index + 1);
    }
  }

  public openLastTab(): void {
    this.nav.select([...this.geneTabs][this.geneTabs.size - 1]);
  }

  public openTabAtIndex(index: number): void {
    this.nav.select([...this.geneTabs][index]);
  }

  public closeTab(event: MouseEvent, tabId: string): void {
    if (tabId === 'autismGenesTool') {
      return;
    }

    if (this.nav.activeId === tabId) {
      this.closeActiveTab();
    } else {
      this.geneTabs.delete(tabId);
    }

    event.preventDefault();
    event.stopImmediatePropagation();
  }

  public closeActiveTab(): void {
    if (this.nav.activeId === 'autismGenesTool') {
      return;
    }

    const index = this.getActiveTabIndex();
    this.geneTabs.delete(this.nav.activeId);

    if ([...this.geneTabs].length === 0) {
      this.openHomeTab();
    } else if ([...this.geneTabs].length === index) {
      this.openLastTab();
    } else {
      this.openTabAtIndex(index);
    }
  }

  public openTabByKey(key: string): void {
    if (this.geneTabs.size === 0) {
      return;
    }

    if (key === '0') {
      this.openLastTab();
    } else if (key === '1') {
      this.openHomeTab();
    } else if (Number(key) - 1 <= this.geneTabs.size) {
      this.openTabAtIndex(Number(key) - 2);
    } else if (key === 'p') {
      this.openPreviousTab();
    } else if (key === 'n') {
      this.openNextTab();
    }
  }

  public getAllCategories(config: AgpTableConfig) {
    const allColumns = [];
    if (config.geneSets) {
      allColumns.push(...config.geneSets.map(obj => obj.displayName));
    }
    if (config.genomicScores) {
      allColumns.push(...config.genomicScores.map(obj => obj.displayName));
    }
    if (config.datasets) {
      allColumns.push(...config.datasets.map(obj => obj.displayName));
    }
    return allColumns;
  }

  public getTableConfig(agpConfig: AgpConfig): AgpTableConfig {
    return new AgpTableConfig(
      agpConfig.defaultDataset,
      cloneDeep(agpConfig.geneSets),
      cloneDeep(agpConfig.genomicScores),
      agpConfig.datasets.map(dataset => {
        const personSets = dataset.personSets.map(personSet => new AgpTableDatasetPersonSet(
          personSet.id,
          personSet.displayName,
          personSet.collectionId,
          personSet.description,
          personSet.parentsCount,
          personSet.childrenCount,
          cloneDeep(dataset.statistics)
        ));
        return new AgpTableDataset(dataset.id, dataset.displayName, dataset.meta, dataset.defaultVisible, personSets);
      }),
      cloneDeep(agpConfig.order)
    );
  }

  public openDropdown(): void {
    this.ngbDropdownMenu.dropdown.open();
    this.multipleSelectMenuComponent.focusSearchInput();
  }

  public handleMultipleSelectMenuApplyEvent($event): void {
    this.shownColumns = $event.data;

    this.shownTableConfig.geneSets = this.tableConfig.geneSets.filter((obj) =>
      this.shownColumns.includes(obj.displayName)
    );
    this.shownTableConfig.genomicScores = this.tableConfig.genomicScores.filter((obj) =>
      this.shownColumns.includes(obj.displayName)
    );
    this.shownTableConfig.datasets = this.tableConfig.datasets.filter((obj) =>
      this.shownColumns.includes(obj.displayName)
    );
    this.shownTableConfig = {...this.shownTableConfig};

    this.ngbDropdownMenu.dropdown.close();
  }

  public tableConfigChangeEvent($event): void {
    this.shownTableConfig = $event;
    this.shownColumns = this.getAllCategories(this.shownTableConfig);
  }
}
