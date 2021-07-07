import { ConfigService } from '../config/config.service';
import { GeneSetsLocalState } from './gene-sets-state';
import { Component, OnInit } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet, GeneSetType } from './gene-sets';
import { Subject, Observable, combineLatest, of } from 'rxjs';
import { DatasetsService } from 'app/datasets/datasets.service';
import { validate } from 'class-validator';
import { Store, Select } from '@ngxs/store';
import { SetGeneSetsValues, GeneSetsModel, GeneSetsState } from './gene-sets.state';
import { switchMap } from 'rxjs/operators';

@Component({
  selector: 'gpf-gene-sets',
  templateUrl: './gene-sets.component.html',
  styleUrls: ['./gene-sets.component.css'],
})
export class GeneSetsComponent implements OnInit {
  geneSetsCollections: Array<GeneSetsCollection>;
  geneSets: Array<GeneSet>;
  private searchQuery: string;

  private geneSetsQueryChange = new Subject<[string, string, Object]>();
  private geneSetsResult: Observable<GeneSet[]>;

  private selectedDatasetId: string;
  private defaultSelectedDenovoGeneSetId: string;

  private geneSetsLocalState = new GeneSetsLocalState();
  @Select(GeneSetsState) state$: Observable<GeneSetsModel>;
  errors: string[] = [];

  constructor(
    private store: Store,
    private config: ConfigService,
    private geneSetsService: GeneSetsService,
    private datasetService: DatasetsService,
  ) { }

  ngOnInit() {
    this.geneSetsService.getGeneSetsCollections().pipe(
      switchMap(geneSetsCollections => {
        return combineLatest(
          of(geneSetsCollections),
          this.datasetService.getSelectedDataset().take(1)
        )
      }),
      switchMap(([geneSetsCollections, dataset]) => {
        return combineLatest(
          of(geneSetsCollections),
          of(dataset),
          this.store.selectOnce(state => state.geneSetsState),
        )
      })
    ).subscribe(([geneSetsCollections, dataset, state]) => {
      this.selectedDatasetId = dataset.id;
      const denovoGeneSetTypes = geneSetsCollections.filter(
        geneSetCollection => geneSetCollection.name === 'denovo'
      )[0].types;

      if (!denovoGeneSetTypes.length) {
        geneSetsCollections = geneSetsCollections.filter(
          (geneSet) => geneSet.name.toLowerCase().trim() !== 'denovo'
        );
      } else {
        denovoGeneSetTypes.sort((a, b) => (a.datasetName > b.datasetName) ? 1 : ((b.datasetName > a.datasetName) ? -1 : 0));

        const selectedStudyTypes = denovoGeneSetTypes.find(
          type => type.datasetId === this.selectedDatasetId
        ) || denovoGeneSetTypes[0];

        if (selectedStudyTypes) {
          this.defaultSelectedDenovoGeneSetId = selectedStudyTypes.datasetId +
            '-' + selectedStudyTypes.peopleGroupId + '-denovo-geneset';
        }
      }
      this.geneSetsCollections = geneSetsCollections;
      this.selectedGeneSetsCollection = geneSetsCollections[0];
      this.restoreState(state);
    });

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

    this.geneSetsResult.subscribe(geneSets => {
      this.geneSets = geneSets.sort((a, b) => a.name.localeCompare(b.name));
      this.store.selectOnce(state => state.geneSetsState).subscribe((state) => {
        if (!state.geneSet || !state.geneSet.geneSet) {
          return;
        }
        for (const geneSet of this.geneSets) {
          if (geneSet.name === state.geneSet.geneSet) {
            this.geneSetsLocalState.geneSet = geneSet;
          }
        }
      });
    });

    this.state$.subscribe(state => {
      validate(this.geneSetsLocalState).then(errors => this.errors = errors.map(err => String(err)));
    });
  }

  restoreState(state) {
    if (state.geneSet && state.geneSetsCollection) {
      for (const geneSetCollection of this.geneSetsCollections) {
        if (geneSetCollection.name === state.geneSetsCollection.name) {
          this.selectedGeneSetsCollection = geneSetCollection;
          this.selectedGeneSet = state.geneSet;
          if (state.geneSetsTypes) {
            this.restoreGeneTypes(state.geneSetsTypes, geneSetCollection);
          }
          this.onSearch();
        }
      }
    } else {
       this.onSearch();
    }
  }

  restoreGeneTypes(geneSetsTypes, geneSetCollection: GeneSetsCollection) {
    const geneTypes = geneSetCollection.types
      .filter(geneType => geneType.datasetId in geneSetsTypes &&
              geneType.peopleGroupId in geneSetsTypes[geneType.datasetId]);
    if (geneTypes.length !== 0) {
      this.geneSetsLocalState.geneSetsTypes = Object.create(null);
      for (const geneType of geneTypes) {
        const datasetId = geneType.datasetId;
        const peopleGroupId = geneType.peopleGroupId;
        for (const peopleGroup of geneType.peopleGroupLegend) {
          if (geneSetsTypes[datasetId][peopleGroupId].indexOf(peopleGroup.id) > -1) {
            this.geneSetsLocalState.select(datasetId, peopleGroupId, peopleGroup.id);
          }
        }
      }
    }
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
      [this.selectedGeneSetsCollection.name, searchTerm, this.geneSetsLocalState.geneSetsTypes]);
  }

  onSelect(event: GeneSet) {
    this.selectedGeneSet = event;
    if (event === null) {
      this.onSearch();
    }
  }

  isSelectedGeneType(datasetId: string, peopleGroupId: string, geneType: string): boolean {
    return this.geneSetsLocalState.isSelected(datasetId, peopleGroupId, geneType);
  }

  setSelectedGeneType(datasetId: string, peopleGroupId: string, geneType: string, value: boolean) {
    this.selectedGeneSet = null;
    if (value) {
      this.geneSetsLocalState.select(datasetId, peopleGroupId, geneType);
    } else {
      this.geneSetsLocalState.deselect(datasetId, peopleGroupId, geneType);
    }
  }

  get selectedGeneSetsCollection(): GeneSetsCollection {
    return this.geneSetsLocalState.geneSetsCollection;
  }

  set selectedGeneSetsCollection(selectedGeneSetsCollection: GeneSetsCollection) {
    this.geneSetsLocalState.geneSetsCollection = selectedGeneSetsCollection;
    this.geneSetsLocalState.geneSet = null;
    this.geneSetsLocalState.geneSetsTypes = Object.create(null);
    this.geneSets = [];

    if (selectedGeneSetsCollection.types.length > 0) {
      const geneSetType = selectedGeneSetsCollection.types.find(genesetType => {
        return genesetType.datasetId === this.selectedDatasetId;
      }) || selectedGeneSetsCollection.types[0];

      this.setSelectedGeneType(geneSetType.datasetId, geneSetType.peopleGroupId,
                               geneSetType.peopleGroupLegend[0].id, true);
    }

    this.onSearch();
  }

  get selectedGeneSet(): GeneSet {
    return this.geneSetsLocalState.geneSet;
  }

  set selectedGeneSet(geneSet) {
    this.geneSetsLocalState.geneSet = geneSet;
    this.store.dispatch(new SetGeneSetsValues(this.geneSetsLocalState));
  }

  getDownloadLink(selectedGeneSet: GeneSet): string {
    return `${this.config.baseUrl}${selectedGeneSet.download}`;
  }

  getGeneSetName(geneType: GeneSetType): string {
    return `${geneType.datasetName}: ${geneType.peopleGroupName}`;
  }
}
