import { GeneSetsLocalState } from './gene-sets-local-state';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet, GeneSetType } from './gene-sets';
import { Subject, Observable, combineLatest, of } from 'rxjs';
import { ValidateNested } from 'class-validator';
import { Store } from '@ngrx/store';
import { catchError, debounceTime, distinctUntilChanged, switchMap, take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { ComponentValidator } from 'app/common/component-validator';
import { selectGeneSets, setGeneSetsValues } from './gene-sets.state';
import { cloneDeep } from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';

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
  public studiesList = new Set<string>();
  public selectedGeneType: GeneSetType;
  public expandedGeneTypes: GeneSetType[] = [];

  public geneSetsQueryChange$ = new Subject<[string, string, object]>();
  private geneSetsResult: Observable<GeneSet[]>;

  private selectedDatasetId: string;
  public downloadUrl: string;
  public geneSetsLoaded = 0;

  public imgPathPrefix = environment.imgPathPrefix;

  @ValidateNested()
  public geneSetsLocalState = new GeneSetsLocalState();

  // The template needs local component reference to use Object static methods
  public object = Object;

  public constructor(
    protected store: Store,
    private geneSetsService: GeneSetsService,
    public modalService: NgbModal,
  ) {
    super(store, 'geneSets', selectGeneSets);
  }

  public ngOnInit(): void {
    this.geneSetsLoaded = null;
    super.ngOnInit();

    this.geneSetsService.getGeneSetsCollections().pipe(
      switchMap(geneSetsCollections => combineLatest([
        of(geneSetsCollections),
        this.store.select(selectGeneSets).pipe(take(1)),
        this.store.select(selectDatasetId).pipe(take(1)),
      ]))
    ).subscribe(([geneSetsCollections, geneSetsState, datasetIdState]) => {
      let geneSetsCollectionsClone = cloneDeep(geneSetsCollections);
      const geneSetsStateClone = cloneDeep(geneSetsState);
      const datasetIdStateClone = cloneDeep(datasetIdState);
      this.selectedDatasetId = datasetIdStateClone;

      const denovoGeneSetTypes = geneSetsCollectionsClone.filter(
        geneSetCollection => geneSetCollection.name === 'denovo'
      )[0].types;

      if (!denovoGeneSetTypes.length) {
        geneSetsCollectionsClone = geneSetsCollectionsClone.filter(
          (geneSet) => geneSet.name.toLowerCase().trim() !== 'denovo'
        );
      } else {
        denovoGeneSetTypes.sort((a, b) => a.datasetName > b.datasetName ? 1 : b.datasetName > a.datasetName ? -1 : 0);

        this.selectedGeneType = denovoGeneSetTypes.find(
          type => type.datasetId === this.selectedDatasetId
        ) || denovoGeneSetTypes[0];

        if (this.selectedGeneType && this.selectedGeneType.children) {
          this.expandedGeneTypes.push(this.selectedGeneType);
        }
      }


      this.geneSetsCollections = geneSetsCollectionsClone;
      this.selectedGeneSetsCollection = geneSetsCollectionsClone[0];
      if (geneSetsStateClone.geneSet) {
        this.restoreState(geneSetsStateClone);
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
            this.geneSetsLocalState.geneSet = geneSet;
            this.isLoading = false;
          }
        }
      });
    });
  }

  private restoreState(state: {
    geneSetsTypes: GeneSetType[];
    geneSetsCollection: GeneSetsCollection;
    geneSet: GeneSet;
}): void {
    if (state.geneSet && state.geneSetsCollection) {
      for (const geneSetCollection of this.geneSetsCollections) {
        if (geneSetCollection.name === state.geneSetsCollection.name) {
          this.selectedGeneSetsCollection = geneSetCollection;
          if (state.geneSetsTypes) {
            this.restoreGeneTypes(state.geneSetsTypes, geneSetCollection);
          }
          // the gene set must be restored last, as that triggers the state update
          // otherwise, sharing a restored state won't work properly
          this.selectedGeneSet = state.geneSet;
          this.onSearch();
        }
      }
    } else {
      this.onSearch();
    }
  }

  private restoreGeneTypes(geneSetsTypes: GeneSetType[], geneSetCollection: GeneSetsCollection): void {
    this.studiesList.clear();
    let restoredGeneTypes = [];
    geneSetCollection.types
      .forEach(geneType => {
        if(geneType.datasetId in geneSetsTypes) {
          restoredGeneTypes.push(geneType);
        }
        restoredGeneTypes.push(...this.restoreAll(geneType, geneSetsTypes));
      });

    if (restoredGeneTypes.length !== 0) {
      this.geneSetsLocalState.geneSetsTypes = Object.create(null);
      for (const geneType of restoredGeneTypes) {
        const datasetId = geneType.datasetId;
        geneType.personSetCollections.forEach(collection => {
          const personSetCollectionId = collection.id;
          for (const personSet of collection.domain) {
            if (geneSetsTypes[datasetId][personSetCollectionId].indexOf(personSet.id) > -1) { 
              this.studiesList.add(`${datasetId}: ${personSetCollectionId}: ${personSet.id}`);
              this.geneSetsLocalState.select(datasetId, personSetCollectionId, personSet.id);
            }
          }
        })
      }
    }
  }

  private restoreAll(type: GeneSetType, geneSetsTypes: GeneSetType[]): GeneSetType[] {
    let restoredChildren = [];
    if(!(type.datasetId in geneSetsTypes) && !type.children) {
      return restoredChildren;
    }

    if(type.datasetId in geneSetsTypes) {
      restoredChildren.push(type);
    }

    if(type.children) {
      type.children.forEach(child => {
        restoredChildren = restoredChildren.concat(this.restoreAll(child, geneSetsTypes));
      });
    }
    return restoredChildren;
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
      [this.selectedGeneSetsCollection.name, this.searchQuery, this.geneSetsLocalState.geneSetsTypes as GeneSetType[]]
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

  public toggleDatasetCollapse(selectedType: GeneSetType): void {
    if(!this.expandedGeneTypes.includes(selectedType)) {
      this.expandedGeneTypes.push(selectedType);
    } else {
      this.hideAll(selectedType)
    }
  }

  private hideAll(type: GeneSetType): void {
    if(!type.children) {
      return;
    }
    if(this.expandedGeneTypes.includes(type)) {
      this.expandedGeneTypes.splice(this.expandedGeneTypes.indexOf(type), 1);
      type.children.forEach(child => {
        this.hideAll(child);
      })
    }
  }

  public select(type: GeneSetType): void {
    this.selectedGeneType = type;
  }

  public removeFromList(study: string): void {
    const removedStudyInfo = study.split(': ');
    this.setSelectedGeneType(removedStudyInfo[0], removedStudyInfo[1], removedStudyInfo[2], false);
  }

  public isSelectedGeneType(datasetId: string, personSetCollectionId: string, geneType: string): boolean {
    return this.geneSetsLocalState.isSelected(datasetId, personSetCollectionId, geneType);
  }

  public setSelectedGeneType(datasetId: string, personSetCollectionId: string, geneType: string, value: boolean): void {
    this.selectedGeneSet = null;
    this.searchQuery = '';
    if (value) {
      this.studiesList.add(`${datasetId}: ${personSetCollectionId}: ${geneType}`);
      this.geneSetsLocalState.select(datasetId, personSetCollectionId, geneType);
    } else {
      this.studiesList.delete(`${datasetId}: ${personSetCollectionId}: ${geneType}`);
      this.geneSetsLocalState.deselect(datasetId, personSetCollectionId, geneType);
    }
  }

  public get selectedGeneSetsCollection(): GeneSetsCollection {
    return this.geneSetsLocalState.geneSetsCollection;
  }

  public set selectedGeneSetsCollection(selectedGeneSetsCollection: GeneSetsCollection) {
    this.geneSetsLocalState.geneSetsCollection = selectedGeneSetsCollection;
    this.geneSetsLocalState.geneSet = null;
    this.geneSetsLocalState.geneSetsTypes = Object.create(null);
    this.geneSets = [];
    this.searchQuery = '';

    if (selectedGeneSetsCollection?.types.length > 0) {
      const geneSetType = selectedGeneSetsCollection.types.find(
        genesetType => genesetType.datasetId === this.selectedDatasetId
      ) || selectedGeneSetsCollection.types[0];

      this.setSelectedGeneType(
        geneSetType.datasetId, geneSetType.personSetCollections[0].id,
        geneSetType.personSetCollections[0].domain[0]?.id as string, true
      );
    }

    this.onSearch();
  }

  public get selectedGeneSet(): GeneSet {
    return this.geneSetsLocalState.geneSet;
  }

  public set selectedGeneSet(geneSet) {
    this.geneSetsLocalState.geneSet = geneSet;
    this.store.dispatch(setGeneSetsValues(this.geneSetsLocalState));
  }

  public getDownloadLink(): string {
    return this.geneSetsService.getGeneSetDownloadLink(this.selectedGeneSet);
  }
}
