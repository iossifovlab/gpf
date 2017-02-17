import {
  GeneSetsState, GENE_SETS_COLLECTION_CHANGE,
  GENE_SET_CHANGE
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

  private geneSetsState: Observable<GeneSetsState>;

  constructor(
    private geneSetsService: GeneSetsService,
    private store: Store<any>
  )  {
    this.geneSetsState = this.store.select('geneSets');
  }

  ngOnInit() {
    this.geneSetsState.subscribe(
      geneSets => {
        if (this.internalSelectedGeneSetsCollection != geneSets.geneSetsCollection) {
          this.internalSelectedGeneSetsCollection = geneSets.geneSetsCollection;
          this.geneSets = null;
          this.onSearch("");
        }
        this.selectedGeneSet = geneSets.geneSet;
      }
    );
    this.geneSetsService.getGeneSetsCollections().subscribe(
      (geneSetsCollections) => {
        this.geneSetsCollections = geneSetsCollections;
    });
  }

  onSearch(searchTerm) {
    this.searchQuery = searchTerm;
    this.geneSetsService.getGeneSets(this.selectedGeneSetsCollection.name, searchTerm).subscribe(
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
