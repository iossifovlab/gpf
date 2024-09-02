import { GeneSetsLocalState } from './gene-sets-local-state';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet, GeneSetType } from './gene-sets';
import { Subject, Observable, combineLatest, of } from 'rxjs';
import { ValidateNested } from 'class-validator';
import { Store } from '@ngrx/store';
import { catchError, debounceTime, distinctUntilChanged, switchMap, take } from 'rxjs/operators';
import { environment } from 'environments/environment';
import { PersonSet } from 'app/datasets/datasets';
import { MatAutocompleteTrigger } from '@angular/material/autocomplete';
import { selectDatasetId } from 'app/datasets/datasets.state';
import { StatefulComponentNgRx } from 'app/common/stateful-component_ngrx';
import { selectGeneSets, setGeneSetsValues } from './gene-sets.state';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css']
})
export class GeneSetsComponent extends StatefulComponentNgRx implements OnInit {
  public geneSetsCollections: Array<GeneSetsCollection>;
  public geneSets: Array<GeneSet>;
  public searchQuery: string;
  public defaultSelectedDenovoGeneSetId: string[] = [];
  public isLoading = true;
  public isDropdownOpen = false;
  @ViewChild('dropdownTrigger') private dropdownTrigger: MatAutocompleteTrigger;
  @ViewChild('searchSetsBox') private searchBox: ElementRef;

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
  ) {
    super(store, 'geneSets', selectGeneSets);
  }

  public ngOnInit(): void {
    this.geneSetsLoaded = null;
    super.ngOnInit();

    this.geneSetsService.getGeneSetsCollections().pipe(
      switchMap(geneSetsCollections => combineLatest(
        of(geneSetsCollections),
        this.store.select(selectGeneSets).pipe(take(1)),
        this.store.select(selectDatasetId).pipe(take(1)),
      ))
    ).subscribe(([geneSetsCollections, geneSetsState, datasetIdState]) => {
      this.selectedDatasetId = datasetIdState;

      const denovoGeneSetTypes = geneSetsCollections.filter(
        geneSetCollection => geneSetCollection.name === 'denovo'
      )[0].types;


      if (!denovoGeneSetTypes.length) {
        geneSetsCollections = geneSetsCollections.filter(
          (geneSet) => geneSet.name.toLowerCase().trim() !== 'denovo'
        );
      } else {
        denovoGeneSetTypes.sort((a, b) => a.datasetName > b.datasetName ? 1 : b.datasetName > a.datasetName ? -1 : 0);

        const selectedStudyTypes = denovoGeneSetTypes.find(
          type => type.datasetId === this.selectedDatasetId
        ) || denovoGeneSetTypes[0];

        if (selectedStudyTypes) {
          this.defaultSelectedDenovoGeneSetId.push(selectedStudyTypes.datasetId +
            '-' + selectedStudyTypes.personSetCollectionId + '-denovo-geneset');
        }
      }

      this.geneSetsCollections = geneSetsCollections;
      this.selectedGeneSetsCollection = geneSetsCollections[0];
      this.restoreState(geneSetsState);
      this.geneSetsLoaded = geneSetsCollections.length;
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
        if (!geneSetsState || !geneSetsState.geneSet) {
          this.isLoading = false;
          return;
        }
        for (const geneSet of this.geneSets) {
          if (geneSet.name === geneSetsState.geneSet.name) {
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
    const geneTypes = geneSetCollection.types
      .filter(geneType => geneType.datasetId in geneSetsTypes &&
              geneType.personSetCollectionId in geneSetsTypes[geneType.datasetId]);
    if (geneTypes.length !== 0) {
      this.geneSetsLocalState.geneSetsTypes = Object.create(null);
      for (const geneType of geneTypes) {
        const datasetId = geneType.datasetId;
        const personSetCollectionId = geneType.personSetCollectionId;
        for (const personSet of geneType.personSetCollectionLegend as PersonSet[]) {
          if (geneSetsTypes[datasetId][personSetCollectionId].indexOf(personSet.id) > -1) {
            const denovoGeneSetId = `${datasetId}-${personSetCollectionId}-denovo-geneset`;
            if (!this.defaultSelectedDenovoGeneSetId.includes(denovoGeneSetId)) {
              this.defaultSelectedDenovoGeneSetId.push(denovoGeneSetId);
            }
            this.geneSetsLocalState.select(datasetId, personSetCollectionId, personSet.id);
          }
        }
      }
    }
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

  public onSearch(): number {
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

  public isSelectedGeneType(datasetId: string, personSetCollectionId: string, geneType: string): boolean {
    return this.geneSetsLocalState.isSelected(datasetId, personSetCollectionId, geneType);
  }

  public setSelectedGeneType(datasetId: string, personSetCollectionId: string, geneType: string, value: boolean): void {
    this.selectedGeneSet = null;
    const intervalId = setInterval(() => {
      if (value) {
        this.geneSetsLocalState.select(datasetId, personSetCollectionId, geneType);
      } else {
        this.geneSetsLocalState.deselect(datasetId, personSetCollectionId, geneType);
      }
      clearInterval(intervalId);
    }, 50);
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
        geneSetType.datasetId, geneSetType.personSetCollectionId,
        geneSetType.personSetCollectionLegend[0].id as string, true
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
