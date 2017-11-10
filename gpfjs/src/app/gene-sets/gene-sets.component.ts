import { ConfigService } from '../config/config.service';
import { GeneSetsState } from './gene-sets-state';
import { Component, OnInit, forwardRef } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { Subject } from 'rxjs/Subject';
import { Observable } from 'rxjs/Observable';
import { toValidationObservable, validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css'],
  providers: [{provide: QueryStateProvider, useExisting: forwardRef(() => GeneSetsComponent) }]
})
export class GeneSetsComponent extends QueryStateProvider implements OnInit {
  geneSetsCollections: Array<GeneSetsCollection>;
  geneSets: Array<GeneSet>;
  private internalSelectedGeneSetsCollection: GeneSetsCollection;
  selectedGeneSet: GeneSet;
  private searchQuery: string;
  private geneSetsTypes: Set<any>;
  private geneSetsState = new GeneSetsState();

  private geneSetsQueryChange = new Subject<[string, string, Array<string>]>();
  private geneSetsResult: Observable<GeneSet[]>;

  errors: string[];
  flashingAlert = false;

  constructor(
    private geneSetsService: GeneSetsService,
    private config: ConfigService,
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  isGeneSetsTypesUpdated(geneSetsTypes: Set<any>): boolean {
    if (!this.geneSetsTypes && geneSetsTypes) {
      return true;
    }
    if (this.geneSetsTypes && !geneSetsTypes) {
      return true;
    }
    if (this.geneSetsTypes.size !== geneSetsTypes.size) {
      return true;
    }
    for (let a in this.geneSetsTypes) {
      if (!geneSetsTypes.has(a)) {
        return true;
      }
    }

    return false;
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name).subscribe(
      (state) => {
        if (state['geneSet'] && state['geneSet']['geneSetsCollection']) {
          for (let geneSetCollection of this.geneSetsCollections) {
            if (geneSetCollection.name === state['geneSet']['geneSetsCollection']) {
              this.geneSetsState.geneSetsCollection = geneSetCollection;
              this.geneSetsState.geneSet = null;

              if (state['geneSet']['geneSetsTypes']) {
                this.restoreGeneTypes(state['geneSet']['geneSetsTypes'], geneSetCollection);
              }
            }
          }
        }
      });
  }

  restoreGeneTypes(geneSetsTypes, geneSetCollection: GeneSetsCollection) {
    let geneTypes = geneSetCollection.types
      .filter(geneType => geneSetsTypes.indexOf(geneType.name) !== -1);
    if (geneTypes.length !== 0) {
      this.geneSetsState.geneSetsTypes = new Set(geneTypes);
      this.geneSetsState.geneSet = null;
    }
  }

  ngOnInit() {

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

          if (this.internalSelectedGeneSetsCollection
            && this.internalSelectedGeneSetsCollection.types.length  > 0
            && geneSets.geneSetsTypes.size == 0) {

            this.geneSets = null;
            refreshData = false;
            this.errors.push("Select at least one gene type");
          } else {
            refreshData = true;
          }
        }

        if (refreshData) {
          this.onSearch(this.searchQuery);
        }
      }
    );

    this.geneSetsService.getGeneSetsCollections().subscribe(
      (geneSetsCollections) => {
        this.geneSetsCollections = geneSetsCollections;
        this.selectedGeneSetsCollection = geneSetsCollections[0];
        this.restoreStateSubscribe();
      }
    );

    this.geneSetsResult = this.geneSetsQueryChange
      .debounceTime(1000)
      .distinctUntilChanged()
      .switchMap(term => {
        return this.geneSetsService.getGeneSets(term[0], term[1], term[2]);
      })
      .catch(error => {
        console.log(error);
        return Observable.of(null);
      });

    this.geneSetsResult.subscribe(
      (geneSets) => {
        this.geneSets = geneSets.sort((a, b) => a.name.localeCompare(b.name));
        this.stateRestoreService.getState(this.constructor.name + 'geneSet').subscribe(
          (state) => {
            if (!state['geneSet'] || !state['geneSet']['geneSet']) {
              return;
            }
            for (let geneSet of this.geneSets) {
              if (geneSet.name === state['geneSet']['geneSet']) {
                this.geneSetsState.geneSet = geneSet;
              }
            }
          }
        );
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

    if (this.geneSets) {
      this.geneSets = this.geneSets.filter(
        (value) => {
          return value.name.indexOf(searchTerm) >= 0 ||
                 value.desc.indexOf(searchTerm) >= 0;
        }
      );
    }

    this.geneSetsQueryChange.next(
      [this.selectedGeneSetsCollection.name, searchTerm, geneSetsTypesNames]);
  }

  onSelect(event: GeneSet) {
    this.geneSetsState.geneSet = event;

    if (event == null) {
      this.onSearch('');
    }
  }

  isSelectedGeneType(geneType): boolean {
    return this.geneSetsTypes.has(geneType);
  }

  setSelectedGeneType(geneType, value) {
    if (value) {
      this.geneSetsState.geneSetsTypes.add(geneType);
    } else {
      this.geneSetsState.geneSetsTypes.delete(geneType);
    }
  }

  get selectedGeneSetsCollection(): GeneSetsCollection {
    return this.internalSelectedGeneSetsCollection;
  }

  set selectedGeneSetsCollection(selectedGeneSetsCollection: GeneSetsCollection) {
    this.geneSetsState.geneSetsCollection = selectedGeneSetsCollection;
    this.geneSetsState.geneSet = null;

    if (selectedGeneSetsCollection.types.length > 0) {
      this.setSelectedGeneType(selectedGeneSetsCollection.types[0], true);
    }
  }

  getDownloadLink(selectedGeneSet: GeneSet): string {
    return `${this.config.baseUrl}${selectedGeneSet.download}`;
  }

  getState() {
    return toValidationObservable(this.geneSetsState).map(geneSetsState => {
        let geneSetsTypes = Array.from(geneSetsState.geneSetsTypes).map(t => t.id);
        return { geneSet : {
            geneSetsCollection: geneSetsState.geneSetsCollection.name,
            geneSet: geneSetsState.geneSet.name,
            geneSetsTypes: geneSetsTypes
          }
        };
      })
      .catch(errors => {
        this.errors = validationErrorsToStringArray(errors);
        this.flashingAlert = true;
        setTimeout(() => { this.flashingAlert = false; }, 1000);

        return Observable.throw(`${this.constructor.name}: invalid state`);
      });
  }
}
