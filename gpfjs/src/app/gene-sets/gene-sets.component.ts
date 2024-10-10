import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import {
  GeneSetsCollection,
  GeneSet,
  GeneSetTypeNode,
  GeneSetType,
  SelectedDenovoTypes,
  SelectedPersonSetCollections } from './gene-sets';
import { Subject, Observable, combineLatest, of } from 'rxjs';
import { IsNotEmpty } from 'class-validator';
import { Store } from '@ngrx/store';
import { catchError, debounceTime, distinctUntilChanged, switchMap, take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { ComponentValidator } from 'app/common/component-validator';
import { selectGeneSets, setGeneSetsValues } from './gene-sets.state';
import { cloneDeep } from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { DatasetsTreeService } from 'app/datasets/datasets-tree.service';
import { DatasetHierarchy } from 'app/datasets/datasets';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css']
})
export class GeneSetsComponent extends ComponentValidator implements OnInit {
  public geneSetsCollections: Array<GeneSetsCollection>;
  public geneSets: Array<GeneSet>;
  public searchQuery: string;
  public isLoading = true;
  public isDropdownOpen = false;
  @ViewChild('dropdownTrigger') private dropdownTrigger: MatAutocompleteTrigger;
  @ViewChild('searchSetsBox') private searchBox: ElementRef;
  public modal: NgbModalRef;
  @ViewChild('denovoModal') public denovoModal: ElementRef;
  public datasetsList = new Set<string>();
  public activeDataset: GeneSetTypeNode;
  public modifiedDatasetIds: Set<string> = new Set<string>();
  public expandedDatasets: GeneSetTypeNode[] = [];
  public denovoDatasetsHierarchy: GeneSetTypeNode[] = [];

  public geneSetsQueryChange$ = new Subject<[string, string, object]>();
  private geneSetsResult: Observable<GeneSet[]>;

  private selectedDatasetId: string;
  public downloadUrl: string;
  public geneSetsLoaded = 0;

  public imgPathPrefix = environment.imgPathPrefix;

  @IsNotEmpty({message: 'Please select a gene set.'})
  public currentGeneSet: GeneSet;
  public currentGeneSetsCollection: GeneSetsCollection;
  public currentGeneSetsTypes: SelectedDenovoTypes[] = new Array<SelectedDenovoTypes>();

  // The template needs local component reference to use Object static methods
  public object = Object;

  public constructor(
    protected store: Store,
    private geneSetsService: GeneSetsService,
    public modalService: NgbModal,
    private datasetsTreeService: DatasetsTreeService,
  ) {
    super(store, 'geneSets', selectGeneSets);
  }

  public ngOnInit(): void {
    this.geneSetsLoaded = null;
    super.ngOnInit();

    combineLatest([
      this.datasetsTreeService.getDatasetHierarchy(),
      this.geneSetsService.getDenovoGeneSets(),
      this.store.select(selectDatasetId).pipe(take(1)),
      this.store.select(selectGeneSets).pipe(take(1)),

    ]).pipe(
      switchMap(([hierarchies, denovoGeneSets, datasetIdState, geneSetsState]) => {
        const datasetIdStateClone = cloneDeep(datasetIdState);
        const geneSetsStateClone = cloneDeep(geneSetsState);
        this.selectedDatasetId = datasetIdStateClone;

        const denovoTypesHierarchy: GeneSetTypeNode[] = [];
        const loadStateTypes = Boolean(geneSetsStateClone.geneSetsTypes);
        hierarchies.forEach(hierarchy => denovoTypesHierarchy.push(
          this.createDenovoGeneSetTypeHierarchy(hierarchy, denovoGeneSets, loadStateTypes)
        ));

        return combineLatest([
          of(denovoTypesHierarchy),
          this.geneSetsService.getGeneSetsCollections(),
          of(geneSetsStateClone),
          of(denovoGeneSets)
        ]);
      })
    ).subscribe(([denovoGeneSetTypesHierarchy, geneSetsCollections, geneSetsState]) => {
      const geneSetsCollectionsClone = cloneDeep(geneSetsCollections);

      this.denovoDatasetsHierarchy = denovoGeneSetTypesHierarchy;

      this.geneSetsCollections = geneSetsCollectionsClone;
      this.selectedGeneSetsCollection = geneSetsCollectionsClone[0];

      if (geneSetsState.geneSet) {
        this.restoreState(geneSetsState);
      } else {
        if (this.denovoDatasetsHierarchy.length) {
          this.activeDataset = this.activeDataset || this.denovoDatasetsHierarchy[0];
          this.expandUntil(this.activeDataset.datasetId, this.denovoDatasetsHierarchy);
        }
      }
      this.geneSetsLoaded = geneSetsCollectionsClone.length;
    });

    this.geneSetsResult = this.geneSetsQueryChange$.pipe(
      distinctUntilChanged(),
      debounceTime(300),
      switchMap(term => this.geneSetsService.getGeneSets(term[0], term[1], term[2])),
      catchError(error => {
        console.warn(error);
        return of(null);
      })
    );

    this.geneSetsResult.subscribe(geneSets => {
      this.geneSets = geneSets.sort((a, b) => a.name.localeCompare(b.name));
      this.store.select(selectGeneSets).pipe(take(1)).subscribe(geneSetsState => {
        const geneSetsStateClone = cloneDeep(geneSetsState);
        if (!geneSetsStateClone || !geneSetsStateClone.geneSet) {
          this.isLoading = false;
          return;
        }
        for (const geneSet of this.geneSets) {
          if (geneSet.name === geneSetsStateClone.geneSet.name) {
            this.currentGeneSet = geneSet;
            this.isLoading = false;
          }
        }
      });
    });
  }

  private createDenovoGeneSetTypeHierarchy(
    hierarchy: DatasetHierarchy,
    denovoGeneSetsTypes: GeneSetType[],
    loadStateTypes: boolean
  ): GeneSetTypeNode {
    if (!hierarchy) {
      return null;
    }

    let children: GeneSetTypeNode[] = [];
    if (hierarchy.children) {
      children = hierarchy.children
        .map(child => this.createDenovoGeneSetTypeHierarchy(child, denovoGeneSetsTypes, loadStateTypes));
    }

    const newGeneSetTypeNode = new GeneSetTypeNode(
      hierarchy.id,
      hierarchy.name,
      denovoGeneSetsTypes.find(type => type.datasetId === hierarchy.id)?.personSetCollections || [],
      children
    );

    if (!loadStateTypes && hierarchy.id === this.selectedDatasetId) {
      this.activeDataset = newGeneSetTypeNode;
    }
    return newGeneSetTypeNode;
  }

  private restoreState(state: {
    geneSetsTypes: SelectedDenovoTypes[];
    geneSetsCollection: GeneSetsCollection;
    geneSet: GeneSet;
}): void {
    if (state.geneSet && state.geneSetsCollection) {
      this.selectedGeneSetsCollection = this.geneSetsCollections.find(collection => collection.name === state.geneSetsCollection.name);
        if (state.geneSetsTypes) {
          this.restoreGeneTypes(state.geneSetsTypes);
        }
        // the gene set must be restored last, as that triggers the state update
        // otherwise, sharing a restored state won't work properly
        this.selectedGeneSet = state.geneSet;
        this.onSearch();
    } else {
      this.onSearch();
    }
  }

  private restoreGeneTypes(geneSetsTypes: SelectedDenovoTypes[]): void {
    this.datasetsList.clear();

    geneSetsTypes.forEach(type => {
      this.expandUntil(type.datasetId, this.denovoDatasetsHierarchy);
      type.collections.forEach(collection => {
        collection.types.forEach(personSetId => {
          this.setSelectedGeneType(type.datasetId, collection.personSetId, personSetId, true);
        });
      });
    });
  }

  private expandUntil(datasetId: string, hierarchy: GeneSetTypeNode[]): boolean {
    let parentExpand = false;
    if(!hierarchy.length) {
      return parentExpand;
    }
    hierarchy.forEach(node => {
      if(node.datasetId === datasetId) {
        parentExpand = true;
      } else {
        const toExpand = this.expandUntil(datasetId, node.children);
        if(toExpand) {
          this.expandedDatasets.push(node);
          parentExpand = true;
        }
      }
    });
    return parentExpand;
  }

  public reset(): void {
    this.searchQuery = '';
    this.selectedGeneSet = null;
    this.isDropdownOpen = true;
    this.onSearch();
  }

  public openCloseDropdown(): void {
    this.isDropdownOpen = !this.dropdownTrigger.panelOpen;
    if (!this.isDropdownOpen) {
      this.dropdownTrigger.closePanel();
    } else {
      this.dropdownTrigger.openPanel();
    }
  }

  public onKeyboardEvent(event: KeyboardEvent): void {
    if (!(event.key === 'ArrowDown' ||
      event.key === 'ArrowUp' ||
      event.key === 'ArrowLeft' ||
      event.key === 'ArrowRight')) {
      this.onSearch();
    }
  }

  public onSearch(): void {
    if (!this.selectedGeneSetsCollection) {
      return;
    }

    if (this.geneSets) {
      this.geneSets = this.geneSets.filter(
        (value) => value.name.indexOf(this.searchQuery) >= 0 || value.desc.indexOf(this.searchQuery) >= 0
      );
    }

    this.isLoading = true;
    this.geneSetsQueryChange$.next(
      [this.selectedGeneSetsCollection.name, this.searchQuery, this.currentGeneSetsTypes]
    );
  }

  public onSelect(event: GeneSet): void {
    this.isDropdownOpen = false;
    (this.searchBox.nativeElement as HTMLElement).blur();
    this.selectedGeneSet = event;
    if (event === null) {
      this.onSearch();
    }
  }

  public openModal(): void {
    if (this.modalService.hasOpenModals()) {
      return;
    }
    this.modal = this.modalService.open(
      this.denovoModal,
      {animation: false, centered: true, windowClass: 'denovo-modal'}
    );
  }

  public toggleDatasetCollapse(selectedType: GeneSetTypeNode): void {
    if (!this.expandedDatasets.includes(selectedType)) {
      this.expandedDatasets.push(selectedType);
    } else {
      this.hideAll(selectedType);
    }
  }

  private hideAll(type: GeneSetTypeNode): void {
    if (!type.children.length) {
      return;
    }
    if (this.expandedDatasets.includes(type)) {
      this.expandedDatasets.splice(this.expandedDatasets.indexOf(type), 1);
      type.children.forEach(child => {
        this.hideAll(child);
      });
    }
  }

  public select(type: GeneSetTypeNode): void {
    this.activeDataset = type;
  }

  public removeFromList(study: string): void {
    const removedStudyInfo = study.split(': ');
    this.setSelectedGeneType(removedStudyInfo[0], removedStudyInfo[1], removedStudyInfo[2], false);
  }

  public isSelectedGeneType(datasetId: string, personSetCollectionId: string, geneType: string): boolean {
    return Boolean(this.currentGeneSetsTypes.find(
      type => type.datasetId === datasetId &&
        type.collections.find(
          collection => collection.personSetId === personSetCollectionId && collection.types.find(
            personSetId => personSetId === geneType))));
  }

  public setSelectedGeneType(datasetId: string, personSetCollectionId: string, geneType: string, value: boolean): void {
    this.selectedGeneSet = null;
    this.searchQuery = '';
    if (value) {
      this.datasetsList.add(`${datasetId}: ${personSetCollectionId}: ${geneType}`);
      this.modifiedDatasetIds.add(datasetId);

      const foundType = this.currentGeneSetsTypes.find(type => type.datasetId === datasetId);
      if (foundType) {
        const foundCollection = foundType.collections.find(
          collection => collection.personSetId === personSetCollectionId
        );
        if (foundCollection) {
          if (!foundCollection.types.includes(geneType)) {
            foundCollection.types.push(geneType);
          }
        } else {
          const newCollection = new SelectedPersonSetCollections(personSetCollectionId, [geneType]);
          foundType.collections.push(newCollection);
        }
      } else {
        const newCollection = new SelectedPersonSetCollections(personSetCollectionId, [geneType]);
        const newSelected = new SelectedDenovoTypes(datasetId, [newCollection]);
        this.currentGeneSetsTypes.push(newSelected);
      }
    } else {
      this.datasetsList.delete(`${datasetId}: ${personSetCollectionId}: ${geneType}`);
      this.modifiedDatasetIds.delete(datasetId);

      const foundType = this.currentGeneSetsTypes.find(type => type.datasetId === datasetId);
      if (foundType) {
        const foundCollection = foundType.collections.find(
          collection => collection.personSetId === personSetCollectionId
        );
        if (foundCollection && foundCollection.types.includes(geneType)) {
          foundCollection.types.splice(foundCollection.types.indexOf(geneType), 1);

          if (!foundCollection.types.length) {
            foundType.collections.splice(foundType.collections.indexOf(foundCollection), 1);

            if (!foundType.collections.length) {
              this.currentGeneSetsTypes.splice(this.currentGeneSetsTypes.indexOf(foundType), 1);
            }
          }
        }
      }
    }
  }

  public get selectedGeneSetsCollection(): GeneSetsCollection {
    return this.currentGeneSetsCollection;
  }

  public set selectedGeneSetsCollection(selectedGeneSetsCollection: GeneSetsCollection) {
    this.currentGeneSetsCollection = selectedGeneSetsCollection;
    this.currentGeneSet = null;
    this.currentGeneSetsTypes = new Array<SelectedDenovoTypes>();
    this.geneSets = [];
    this.searchQuery = '';

    if (selectedGeneSetsCollection.name === 'denovo' &&
      this.activeDataset &&
      this.activeDataset.personSetCollections.length) {
      this.setSelectedGeneType(
        this.activeDataset.datasetId, this.activeDataset.personSetCollections[0].personSetCollectionId,
        this.activeDataset.personSetCollections[0].personSetCollectionLegend[0]?.id, true
      );
    }

    this.onSearch();
  }

  public get selectedGeneSet(): GeneSet {
    return this.currentGeneSet;
  }

  public set selectedGeneSet(geneSet) {
    this.currentGeneSet = geneSet;
    this.store.dispatch(setGeneSetsValues({
      geneSet: this.currentGeneSet,
      geneSetsCollection: this.currentGeneSetsCollection,
      geneSetsTypes: cloneDeep(this.currentGeneSetsTypes)
    }));
  }

  public getDownloadLink(): string {
    return this.geneSetsService.getGeneSetDownloadLink(this.selectedGeneSet);
  }
}
