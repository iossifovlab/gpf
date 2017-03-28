import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { ConfigService } from '../config/config.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';
import { QueryData } from './query';

let FIELD_TO_OBJECT_PROPERTY = [
  ["family id", "familyId"],
  ["study", "study"],
  ["study phenotype", "studyPhenotype"],
  ["location", "location"],
  ["variant", "variant"],
  ["family genotype", "familyGenotype"],
  ["from parent", "fromParent"],
  ["in child", "inChild"],
  ["worst requested effect", "worstRequestedEffect"],
  ["genes", "genes"],
  ["count", "count"],
  ["all effects", "allEffects"],
  ["requested effects", "requestedEffects"],
  ["population type", "populationType"],
  ["worst effect type", "worstEffectType"],
  ["effect details", "effectDetails"],
  ["alternative allele frequency", "alternativeAlleleFrequency"],
  ["number of alternative alleles", "alternativeAllelesCount"],
  ["SSCfreq", "SSCfreqWithoutNan"],
  ["EVSfreq", "EVSfreqWithoutNan"],
  ["E65freq", "E65freqWithoutNan"],
  ["number of genotyped parents", "genotypedParentsCount"],
  ["children description", "childrenDescription"],
  ["validation status", "validationStatus"],
  ["_pedigree_", "pedigreeDataFromArray"],
  ["phenoInChS", "phenoInChS"]
];

@Injectable()
export class QueryService {
  private genotypePreviewUrl = 'genotype_browser/preview';

  private headers = new Headers({ 'Content-Type': 'application/json' });
  private fieldToObjectPropertyMap = new Map<string, string>();

  constructor(
    private http: Http,
    private config: ConfigService
  ) {
    for (let idx in FIELD_TO_OBJECT_PROPERTY) {
      this.fieldToObjectPropertyMap.set(
        FIELD_TO_OBJECT_PROPERTY[idx][0],
        FIELD_TO_OBJECT_PROPERTY[idx][1]);
    }
  }

  private parseGenotypePreviewResponse(response: Response): GenotypePreviewsArray {
    let data = response.json();
    if (data.count === 0) {
      return new GenotypePreviewsArray(0, null);
    }
    if (data.cols === undefined) {
      return new GenotypePreviewsArray(0, null);
    }

    let genotypePreviewsArray = new GenotypePreviewsArray(data.count, data.legend);

    for (let row in data.rows) {
      let genotypePreview = new GenotypePreview();
      for (let elem in data.rows[row]) {
        let propertyName = this.fieldToObjectPropertyMap.get(data.cols[elem]);
        let propertyValue = data.rows[row][elem];

        if (propertyName) {
          genotypePreview[propertyName] = propertyValue;
        }
        else {
          genotypePreview.additionalData[data.cols[elem]] = propertyValue
        }
      }

      genotypePreviewsArray.genotypePreviews.push(genotypePreview);
    }
    console.log(genotypePreviewsArray)
    return genotypePreviewsArray;
  }

  getGenotypePreviewByFilter(filter: QueryData): Observable<GenotypePreviewsArray> {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers, withCredentials: true });

    return this.http.post(this.genotypePreviewUrl, filter, options)
      .map(res => {
        return this.parseGenotypePreviewResponse(res)
      });
  }
}
