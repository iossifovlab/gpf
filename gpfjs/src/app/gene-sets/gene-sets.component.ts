import {
  GeneSetsState, GENE_SETS_COLLECTION_CHANGE,
  GENE_SET_CHANGE, GENE_SETS_TYPES_ADD, GENE_SETS_TYPES_REMOVE
} from './gene-sets-state';
import { Component } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { Observable } from 'rxjs';
import { Store } from '@ngrx/store';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css']
})
export class GeneSetsComponent {
  private geneSetsCollections: Array<GeneSetsCollection>;
  private geneSets: Array<GeneSet>;
  private internalSelectedGeneSetsCollection: GeneSetsCollection;
  private selectedGeneSet: GeneSet;
  private searchQuery: string;
  private geneSetsTypes: Set<any>;
  private geneSetsState: Observable<GeneSetsState>;


  constructor(
    private geneSetsService: GeneSetsService,
    private store: Store<any>
  )  {
    this.geneSetsState = this.store.select('geneSets');
  }

  isGeneSetsTypesUpdated(geneSetsTypes: Set<any>): boolean {
    if (!this.geneSetsTypes && geneSetsTypes) return true;
    if (this.geneSetsTypes && !geneSetsTypes) return true;
    if (this.geneSetsTypes.size !== geneSetsTypes.size) return true;
    for (var a in this.geneSetsTypes) {
      if (!geneSetsTypes.has(a)) return true;
    }

    return false;
  }

  ngOnInit() {
    this.geneSetsState.subscribe(
      geneSets => {
        let refreshData = false;

        if (this.internalSelectedGeneSetsCollection != geneSets.geneSetsCollection) {
          this.internalSelectedGeneSetsCollection = geneSets.geneSetsCollection;
          this.geneSets = null;
          this.searchQuery = "";
          refreshData = true;
        }
        this.selectedGeneSet = geneSets.geneSet;

        if (this.isGeneSetsTypesUpdated(geneSets.geneSetsTypes)) {
          this.geneSetsTypes = geneSets.geneSetsTypes;
          refreshData = true;
        }

        if (refreshData) {
          this.onSearch(this.searchQuery);
        }
      }
    );
    this.geneSetsService.getGeneSetsCollections().subscribe(
      (geneSetsCollections) => {
        this.geneSetsCollections = geneSetsCollections;
    });
  }

  onSearch(searchTerm) {
    if (!this.selectedGeneSetsCollection) return;

    this.searchQuery = searchTerm;
    this.geneSets = null;
    this.geneSetsService.getGeneSets(this.selectedGeneSetsCollection.name, searchTerm, this.geneSetsTypes).subscribe(
      (geneSets) => {
        this.geneSets = geneSets.sort((a, b) => a.name.localeCompare(b.name));
    });
  }

  onSelect(event: GeneSet) {
    this.store.dispatch({
      'type': GENE_SET_CHANGE,
      'payload': event
    });
  }

  isSelectedGeneType(geneType): boolean {
    return this.geneSetsTypes.has(geneType);
  }

  setSelectedGeneType(geneType, value) {
    this.store.dispatch({
      'type': value ? GENE_SETS_TYPES_ADD : GENE_SETS_TYPES_REMOVE ,
      'payload': geneType
    });
  }

  get selectedGeneSetsCollection(): GeneSetsCollection {
    return this.internalSelectedGeneSetsCollection;
  }

  set selectedGeneSetsCollection(selectedGeneSetsCollection: GeneSetsCollection) {
    this.store.dispatch({
      'type': GENE_SETS_COLLECTION_CHANGE,
      'payload': selectedGeneSetsCollection
    });
  }
}
