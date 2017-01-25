import { Injectable } from '@angular/core';
import { Headers, Http, Response, RequestOptions } from '@angular/http';
import { Observable } from 'rxjs';

import 'rxjs/add/operator/toPromise';

import { ConfigService } from '../config/config.service';
import { GenotypePreview, GenotypePreviewsArray } from '../genotype-preview-table/genotype-preview';

let FIELD_TO_OBJECT_PROPERTY = [
    [ "family id", "familyId" ],
    [ "study", "study" ],
    [ "study phenotype", "studyPhenotype" ],
    [ "location", "location" ],
    [ "variant", "variant" ],
    [ "family genotype", "familyGenotype" ],
    [ "from parent", "fromParent" ],
    [ "in child", "inChild" ],
    [ "worst requested effect", "worstRequestedEffect" ],
    [ "genes", "genes" ],
    [ "count", "count" ],
    [ "all effects", "allEffects" ],
    [ "requested effects", "requestedEffects" ],
    [ "population type", "populationType" ],
    [ "worst effect type", "worstEffectType" ],
    [ "effect details", "effectDetails" ],
    [ "alternative allele frequency", "alternativeAlleleFrequency" ],
    [ "number of alternative alleles", "alternativeAllelesCount" ],
    [ "SSCfreq", "SSCfreq" ],
    [ "EVSfreq", "EVSfreq" ],
    [ "E65freq", "E65freq" ],
    [ "number of genotyped parents", "genotypedParentsCount" ],
    [ "parent races", "parentRaces" ],
    [ "children description", "childrenDescription" ],
    [ "proband verbal iq", "probandVerbalIQ" ],
    [ "proband non-verbal iq", "porbandNonVerbalIQ" ],
    [ "validation status", "validationStatus" ],
    [ "_pedigree_", "pedigree" ],
    [ "phenoInChS", "phenoInChS"]
];

@Injectable()
export class QueryService {
  private genotypePreviewUrl = 'we_query_variants_preview';

  private headers = new Headers({ 'Content-Type': 'application/json' });
  private fieldToObjectPropertyMap = new Map<string, string>();

  constructor(
    private http: Http,
    private config: ConfigService
  ) {
    for (let idx in FIELD_TO_OBJECT_PROPERTY){
      this.fieldToObjectPropertyMap.set(FIELD_TO_OBJECT_PROPERTY[idx][0], FIELD_TO_OBJECT_PROPERTY[idx][1]);
    }
  }

  private handleGenotypePreviewError(error: any): GenotypePreviewsArray {
    console.error('error while parsing Genotype Preview response: ', error);
    return new GenotypePreviewsArray(0);
  }

  private parseGenotypePreviewResponse = (response: Response): GenotypePreviewsArray => {

    let data = response.json();
    if (data.count === 0) {
      return new GenotypePreviewsArray(0);
    }
    if (data.cols === undefined) {
      return new GenotypePreviewsArray(0);
    }
    
    let genotypePreviewsArray = new GenotypePreviewsArray(data.count);
    
    for (let row in data.rows) {
      let genotypePreview = new GenotypePreview();
      for (let elem in data.rows[row]) {
        let propertyName = this.fieldToObjectPropertyMap.get(data.cols[elem]);
        let propertyValue = data.rows[row][elem];
        genotypePreview[propertyName] = propertyValue;
      }
      
      genotypePreviewsArray.genotypePreviews.push(genotypePreview);
    }
        
    return genotypePreviewsArray;
  }

  getGenotypePreviewByFilter(): Promise<GenotypePreviewsArray> {
    let headers = new Headers({ 'Content-Type': 'application/json' });
    let options = new RequestOptions({ headers: headers });
    
    return this.http.post(this.genotypePreviewUrl, {}, options)
      .toPromise()
      .then(this.parseGenotypePreviewResponse)
      .catch(this.handleGenotypePreviewError);
  }
}
