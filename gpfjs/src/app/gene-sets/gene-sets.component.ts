import { ConfigService } from '../config/config.service';
import {
  GeneSetsState, GENE_SETS_INIT, GENE_SETS_COLLECTION_CHANGE,
  GENE_SET_CHANGE, GENE_SETS_TYPES_ADD, GENE_SETS_TYPES_REMOVE
} from './gene-sets-state';
import { Component, OnInit, forwardRef } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { Subject } from 'rxjs/Subject';
import { Observable } from 'rxjs/Observable';
import { Store } from '@ngrx/store';
import { toObservableWithValidation, validationErrorsToStringArray } from '../utils/to-observable-with-validation'
import { ValidationError } from "class-validator";
import { QueryStateProvider } from '../query/query-state-provider'

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GeneSetsComponent) }]
})
export class GeneSetsComponent extends QueryStateProvider implements OnInit {
  private geneSetsCollections: Array<GeneSetsCollection>;
  private geneSets: Array<GeneSet>;
  private internalSelectedGeneSetsCollection: GeneSetsCollection;
  private selectedGeneSet: GeneSet;
  private searchQuery: string;
  private geneSetsTypes: Set<any>;
  private geneSetsState: Observable<[GeneSetsState, boolean, ValidationError[]]>;

  private geneSetsQueryChange = new Subject<[string, string, Array<string>]>();
  private geneSetsResult: Observable<GeneSet[]>;

  private errors: string[];

  constructor(
    private geneSetsService: GeneSetsService,
    private store: Store<any>,
    private config: ConfigService,
  ) {
    super();
    this.geneSetsState = toObservableWithValidation(GeneSetsState, this.store.select('geneSets'));
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
    this.store.dispatch({
      'type': GENE_SETS_INIT,
    });

    this.geneSetsState.subscribe(
      ([geneSets, isValid, validationErrors])  => {
        if (geneSets == null) {
          return;
        }
        this.errors = validationErrorsToStringArray(validationErrors);

        let refreshData = false;

        if (this.internalSelectedGeneSetsCollection !== geneSets.geneSetsCollection) {
          this.internalSelectedGeneSetsCollection = geneSets.geneSetsCollection;
          this.geneSets = null;
          this.searchQuery = '';
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

    this.geneSetsResult = this.geneSetsQueryChange
      .debounceTime(1000)
      .distinctUntilChanged()
      .switchMap(term => {
        return this.geneSetsService.getGeneSets(term[0], term[1], term[2]);
      })
      .catch(error => {
        console.log(error);
        return null;
      });

    this.geneSetsResult.subscribe(
      (geneSets) => {
        this.geneSets = geneSets.sort((a, b) => a.name.localeCompare(b.name));
      });
  }

  onSearch(searchTerm: string) {
    if (!this.selectedGeneSetsCollection) {
      return;
    }

    let geneSetsTypesNames = new Array<string>();
    this.geneSetsTypes.forEach((value) => {
      geneSetsTypesNames.push(value.id);
    });

    this.searchQuery = searchTerm;
    this.geneSets = null;

    this.geneSetsQueryChange.next(
      [this.selectedGeneSetsCollection.name, searchTerm, geneSetsTypesNames]);
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
      'type': value ? GENE_SETS_TYPES_ADD : GENE_SETS_TYPES_REMOVE,
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

  getDownloadLink(selectedGeneSet: GeneSet): string {
    return `${this.config.baseUrl}${selectedGeneSet.download}`;
  }

  getState() {
    return this.geneSetsState.take(1).map(
      ([geneSetsState, isValid, validationErrors]) => {
        if (!isValid) {
          throw "invalid state"
        }

        let geneSetsTypes = Array.from(geneSetsState.geneSetsTypes).map(t => t.id);
        return { geneSet :{
          geneSetsCollection: geneSetsState.geneSetsCollection.name,
          geneSet: geneSetsState.geneSet.name,
          geneSetsTypes: geneSetsTypes
        }};
    });
  }
}
