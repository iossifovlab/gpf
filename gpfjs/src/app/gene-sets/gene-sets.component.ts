import { ConfigService } from '../config/config.service';
import { GeneSetsState } from './gene-sets-state';
import { Component, OnInit, forwardRef } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet } from './gene-sets';
import { Subject } from 'rxjs/Subject';
import { Observable } from 'rxjs/Observable';
import { validationErrorsToStringArray } from '../utils/to-observable-with-validation';
import { ValidationError } from 'class-validator';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css'],
  providers: [{
    provide: QueryStateProvider,
    useExisting: forwardRef(() => GeneSetsComponent)
  }]
})
export class GeneSetsComponent extends QueryStateWithErrorsProvider implements OnInit {
  geneSetsCollections: Array<GeneSetsCollection>;
  geneSets: Array<GeneSet>;
  private internalSelectedGeneSetsCollection: GeneSetsCollection;
  private searchQuery: string;
  private geneSetsState = new GeneSetsState();

  private geneSetsQueryChange = new Subject<[string, string, Object]>();
  private geneSetsResult: Observable<GeneSet[]>;

  constructor(
    private geneSetsService: GeneSetsService,
    private config: ConfigService,
    private stateRestoreService: StateRestoreService
  ) {
    super();
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['geneSet'] && state['geneSet']['geneSetsCollection']) {
          for (let geneSetCollection of this.geneSetsCollections) {
            if (geneSetCollection.name === state['geneSet']['geneSetsCollection']) {
              this.geneSetsState.geneSetsCollection = geneSetCollection;

              if (state['geneSet']['geneSetsTypes']) {
                this.restoreGeneTypes(state['geneSet']['geneSetsTypes'], geneSetCollection);
              }
              this.onSearch();
            }
          }
        } else {
           this.onSearch();
        }
      });
  }

  restoreGeneTypes(geneSetsTypes, geneSetCollection: GeneSetsCollection) {
    let geneTypes = geneSetCollection.types
      .filter(geneType => geneType.datasetId in geneSetsTypes);
    if (geneTypes.length !== 0) {
      this.geneSetsState.geneSetsTypes = Object.create(null);
      for (let geneType of geneTypes) {
        let datasetId = geneType.datasetId;
        for (let phenotype of geneType.phenotypes) {
          if (geneSetsTypes[datasetId].indexOf(phenotype.id) > -1) {
            this.geneSetsState.select(datasetId, phenotype.id);
          }
        }
      }
    }
  }

  ngOnInit() {
    this.geneSetsService.getGeneSetsCollections().subscribe(
      (geneSetsCollections) => {
        this.geneSetsCollections = geneSetsCollections;
        this.selectedGeneSetsCollection = geneSetsCollections[0];
        this.restoreStateSubscribe();
      }
    );

    this.geneSetsResult = this.geneSetsQueryChange
      .distinctUntilChanged()
      .debounceTime(300)
      .switchMap(term => {
        return this.geneSetsService.getGeneSets(term[0], term[1], term[2]);
      })
      .catch(error => {
        console.warn(error);
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

  onSearch(searchTerm = '') {
    if (!this.selectedGeneSetsCollection) {
      return;
    }

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
      [this.selectedGeneSetsCollection.name, searchTerm, this.geneSetsState.geneSetsTypes]);
  }

  onSelect(event: GeneSet) {
    this.geneSetsState.geneSet = event;

    if (event == null) {
      this.onSearch();
    }
  }

  isSelectedGeneType(datasetId: string, geneType: string): boolean {
    return this.geneSetsState.isSelected(datasetId, geneType);
  }

  setSelectedGeneType(datasetId: string, geneType: string, value: boolean) {
    if (value) {
      this.geneSetsState.select(datasetId, geneType);
    } else {
      this.geneSetsState.deselect(datasetId, geneType);
    }
  }

  get selectedGeneSetsCollection(): GeneSetsCollection {
    return this.geneSetsState.geneSetsCollection;
  }

  set selectedGeneSetsCollection(selectedGeneSetsCollection: GeneSetsCollection) {
    this.geneSetsState.geneSetsCollection = selectedGeneSetsCollection;
    this.geneSetsState.geneSet = null;
    this.geneSetsState.geneSetsTypes = Object.create(null);
    this.geneSets = [];

    if (selectedGeneSetsCollection.types.length > 0) {
      let geneSetType = selectedGeneSetsCollection.types[0];
      this.setSelectedGeneType(geneSetType.datasetId, geneSetType.phenotypes[0].id, true);
    }
    this.onSearch();
  }

  get selectedGeneSet(): GeneSet {
    return this.geneSetsState.geneSet;
  }

  set selectedGeneSet(geneSet) {
    this.geneSetsState.geneSet = geneSet;
  }

  getDownloadLink(selectedGeneSet: GeneSet): string {
    return `${this.config.baseUrl}${selectedGeneSet.download}`;
  }

  getState() {
    return this.validateAndGetState(this.geneSetsState)
      .map(geneSetsState => {
        return {
          geneSet : {
            geneSetsCollection: geneSetsState.geneSetsCollection.name,
            geneSet: geneSetsState.geneSet.name,
            geneSetsTypes: geneSetsState.geneSetsTypes
          }
        };
      });
  }
}
