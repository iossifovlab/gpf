import { Component, OnInit } from '@angular/core';
import { QueryService } from '../query/query.service';
import { GenotypePreview, GenotypePreviewsArray } from './genotype-preview';
import { GpfComparatorInterface } from '../table/comparator.interface';



class LocationComparator implements GpfComparatorInterface {
  compare(leftVal: any, rightVal: any): Number {
    return 1;
  }
}

@Component({
  selector: 'gpf-genotype-preview-table',
  templateUrl: './genotype-preview-table.component.html',
  styleUrls: ['./genotype-preview-table.component.css']
})
export class GenotypePreviewTableComponent implements OnInit {
  private genotypePreviewsArray: GenotypePreviewsArray
  private locationComparator: LocationComparator;

  constructor(
    private queryService: QueryService
  ) { }

  ngOnInit() {
    this.queryService.getGenotypePreviewByFilter()
    .then(genotypePreviewsArray => {
      this.genotypePreviewsArray = genotypePreviewsArray
    });
  }
  
  createLocationComparator(): GpfComparatorInterface {
    return this.locationComparator;
  }
}
