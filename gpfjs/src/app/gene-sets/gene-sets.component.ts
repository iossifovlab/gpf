import { ConfigService } from '../config/config.service';
import { GeneSetsState } from './gene-sets-state';
import { Component, OnInit, forwardRef } from '@angular/core';
import { GeneSetsService } from './gene-sets.service';
import { GeneSetsCollection, GeneSet, GeneSetType } from './gene-sets';
import { Subject ,  Observable } from 'rxjs';
import { QueryStateProvider, QueryStateWithErrorsProvider } from '../query/query-state-provider';
import { StateRestoreService } from '../store/state-restore.service';
import { DatasetsService } from 'app/datasets/datasets.service';

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
  private searchQuery: string;
  private geneSetsState = new GeneSetsState();

  private geneSetsQueryChange = new Subject<[string, string, Object]>();
  private geneSetsResult: Observable<GeneSet[]>;

  private selectedDatasetId: string;
  private defaultSelectedDenovoGeneSetId: string;

  constructor(
    private geneSetsService: GeneSetsService,
    private config: ConfigService,
    private stateRestoreService: StateRestoreService,
    private datasetService: DatasetsService
  ) {
    super();
  }

  restoreStateSubscribe() {
    this.stateRestoreService.getState(this.constructor.name)
      .take(1)
      .subscribe(state => {
        if (state['geneSet'] && state['geneSet']['geneSetsCollection']) {
          for (const geneSetCollection of this.geneSetsCollections) {
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
    const geneTypes = geneSetCollection.types
      .filter(geneType => geneType.datasetId in geneSetsTypes &&
              geneType.peopleGroupId in geneSetsTypes[geneType.datasetId]);
    if (geneTypes.length !== 0) {
      this.geneSetsState.geneSetsTypes = Object.create(null);
      for (const geneType of geneTypes) {
        const datasetId = geneType.datasetId;
        const peopleGroupId = geneType.peopleGroupId;
        for (const peopleGroup of geneType.peopleGroupLegend) {
          if (geneSetsTypes[datasetId][peopleGroupId].indexOf(peopleGroup.id) > -1) {
            this.geneSetsState.select(datasetId, peopleGroupId, peopleGroup.id);
          }
        }
      }
    }
  }

  ngOnInit() {
    this.geneSetsService.getGeneSetsCollections().subscribe(
      (geneSetsCollections) => {
        const dataset$ = this.datasetService.getSelectedDataset();
        dataset$.take(1).subscribe(dataset => {
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
          this.restoreStateSubscribe();
        });
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
            for (const geneSet of this.geneSets) {
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

  isSelectedGeneType(datasetId: string, peopleGroupId: string, geneType: string): boolean {
    return this.geneSetsState.isSelected(datasetId, peopleGroupId, geneType);
  }

  setSelectedGeneType(datasetId: string, peopleGroupId: string, geneType: string, value: boolean) {
    this.selectedGeneSet = null;
    if (value) {
      this.geneSetsState.select(datasetId, peopleGroupId, geneType);
    } else {
      this.geneSetsState.deselect(datasetId, peopleGroupId, geneType);
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
      const geneSetType = selectedGeneSetsCollection.types.find(genesetType => {
        return genesetType.datasetId === this.selectedDatasetId;
      }) || selectedGeneSetsCollection.types[0];

      this.setSelectedGeneType(geneSetType.datasetId, geneSetType.peopleGroupId,
                               geneSetType.peopleGroupLegend[0].id, true);
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

  getGeneSetName(geneType: GeneSetType): string {
    return `${geneType.datasetName}: ${geneType.peopleGroupName}`;
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
