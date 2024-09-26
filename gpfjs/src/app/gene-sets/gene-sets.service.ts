import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { GeneSetsCollection, GeneSet, GeneSetJson, GeneSetType } from './gene-sets';
import { ConfigService } from '../config/config.service';
import { map } from 'rxjs/operators';
import { PersonSetCollection } from 'app/datasets/datasets';

@Injectable()
export class GeneSetsService {
  private readonly geneSetsCollectionsUrl = 'gene_sets/gene_sets_collections';
  private readonly geneSetsSearchUrl = 'gene_sets/gene_sets';

  public constructor(
    private http: HttpClient,
    private config: ConfigService,
  ) {}

  public getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
    const newCollection = new GeneSetsCollection('autism', 'Autism Gene Sets', []);
    const types: GeneSetType[] = [];

    const basicPersonSetCollection = new PersonSetCollection('phenotype', 'Phenotype', [
      {
        id: 'autism',
        name: 'autism',
        values: [
          'affected'
        ],
        color: '#ff2121'
      },
      {
        id: 'unaffected',
        name: 'unaffected',
        values: [
          'unaffected'
        ],
        color: '#ffffff'
      }
  ]);

    const spark1 = new GeneSetType('SFARI_SPARK_WES_1_CSHL', 'SPARK CSHL WES batch 1', [basicPersonSetCollection], null);
    const spark2 = new GeneSetType('iWES_v2_genotypes', 'SPARK Consortium iWES v2', [], null);
    const sparkDataset = new GeneSetType('SPARK_genotypes', 'SPARK Genotypes', [basicPersonSetCollection], [spark1, spark2]);

    const sscEichler = new GeneSetType('EichlerTG2012_liftover', 'SSC Eichler2012 TG de Novo liftover', [basicPersonSetCollection], null);
    const sscKrumm = new GeneSetType('Krumm2015_SNVindel_liftover', 'SSC Krumm2015 WES de Novo liftover', [basicPersonSetCollection], null);
    const sscWesDataset = new GeneSetType('SSC_WES', 'SSC WES', [basicPersonSetCollection], [sscEichler, sscKrumm]);

    const sscDataset = new GeneSetType('SSC_genotypes', 'SSC Genotypes', [basicPersonSetCollection], [sscWesDataset]);

    const singleStudyPersonSetCollection = new PersonSetCollection('phenotype', 'Phenotype', [
      {
        "id": "aspergers_disorder",
        "name": "aspergers disorder",
        "values": [
            "aspergers-disorder"
        ],
        "color": "#9d8c00"
    },
    {
        "id": "autistic_disorder",
        "name": "autistic disorder",
        "values": [
            "autistic-disorder"
        ],
        "color": "#ff2121"
    },
    {
        "id": "non_spectrum_dx",
        "name": "non-spectrum dx",
        "values": [
            "non-spectrum-dx"
        ],
        "color": "#aca8cf"
    },
    {
        "id": "pdd_nos_atypical_autism",
        "name": "PDD-NOS atypical autism",
        "values": [
            "pdd-nos-atypical-autism"
        ],
        "color": "#0200a2"
    },
    {
        "id": "no_diagnosis",
        "name": "no diagnosis",
        "values": [
            "no-diagnosis"
        ],
        "color": "#ffffff"
    }
  ]);

  const singleStudyPersonSetCollection2 = new PersonSetCollection('status_16p', '16p status', [
    {
      "id": "deletion",
      "name": "deletion",
      "values": [
          "deletion"
      ],
      "color": "#ff2121"
  },
  {
      "id": "duplication",
      "name": "duplication",
      "values": [
          "duplication"
      ],
      "color": "#ac6bad"
  },
  {
      "id": "triplication",
      "name": "triplication",
      "values": [
          "triplication"
      ],
      "color": "#ffe502"
  },
  {
      "id": "negative",
      "name": "negative",
      "values": [
          "negative"
      ],
      "color": "#ffffff"
  }
])

    const singleStudy = new GeneSetType('SFARI_SVIP_WES_1_liftover', 'Simons Searchlight WES liftover', [singleStudyPersonSetCollection, singleStudyPersonSetCollection2] , null);

    types.push(singleStudy);
    types.push(sparkDataset);
    types.push(sscDataset);
    const newCollection2 = new GeneSetsCollection('denovo', 'Denovo', types);

    const result: GeneSetsCollection[] = [];
    result.push(newCollection, newCollection2);
    return of(result);

    // to check if fromJson will work after refactor
    // return of(mockResponse as GeneSetCollectionJson[]).pipe(map(res => GeneSetsCollection.fromJsonArray(res)));
  }

  // public getGeneSetsCollections(): Observable<GeneSetsCollection[]> {
  //   // eslint-disable-next-line @typescript-eslint/naming-convention
  //   const headers = { 'Content-Type': 'application/json' };
  //   const options = { headers: headers, withCredentials: true };

  //   return this.http
  //     .get<GeneSetCollectionJson[]>(this.config.baseUrl + this.geneSetsCollectionsUrl, options)
  //     .pipe(map(res => GeneSetsCollection.fromJsonArray(res)));
  // }

  public getGeneSets(
    selectedGeneSetsCollection: string,
    searchTerm: string,
    geneSetsTypes: object
  ): Observable<GeneSet[]> {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const headers = { 'Content-Type': 'application/json' };
    const options = { headers: headers, withCredentials: true };

    return this.http
      .post<GeneSetJson[]>(this.config.baseUrl + this.geneSetsSearchUrl, {
        geneSetsCollection: selectedGeneSetsCollection,
        filter: searchTerm,
        geneSetsTypes: geneSetsTypes,
        limit: 100
      }, options)
      .pipe(map(res => GeneSet.fromJsonArray(res)));
  }

  public getGeneSetDownloadLink(geneSet: GeneSet): string {
    return `${this.config.baseUrl}${geneSet.download}`;
  }
}
