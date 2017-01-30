import { Component, OnInit } from '@angular/core';
import { QueryService } from '../query/query.service';
import { GenotypePreview, GenotypePreviewsArray } from './genotype-preview';

@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css']
})
export class GenotypePreviewTableComponent implements OnInit {
  private genotypePreviewsArray: GenotypePreviewsArray

  constructor(
    private queryService: QueryService
  ) { }

  ngOnInit() {
    this.queryService.getGenotypePreviewByFilter()
    .then(genotypePreviewsArray => {
      this.genotypePreviewsArray = genotypePreviewsArray
    });
  }
  
  locationComparator(a: any, b: any): number {
    let XYMStringToNum = (str:string): number => {
      if (str == "X") return 100;
      if (str == "Y") return 101;
      if (str == "M") return 102;
      return +str;
    };
  
    let leftVar = a.location;
    let rightVar = b.location;
    
    let leftArr = leftVar.split(":");
    let rightArr = rightVar.split(":");
    
    if (leftArr[0] == rightArr[0]) {
      return +leftArr[1] - +rightArr[1]; 
    }
    else {
      return XYMStringToNum(leftArr[0]) - XYMStringToNum(rightArr[0]);
    }
    
  }
}
