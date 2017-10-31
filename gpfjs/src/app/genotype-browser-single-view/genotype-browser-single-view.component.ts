import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';

@Component({
  selector: 'gpf-genotype-browser-single-view',
  templateUrl: './genotype-browser-single-view.component.html',
  styleUrls: ['./genotype-browser-single-view.component.css']
})
export class GenotypeBrowserSingleViewComponent implements OnInit {

  private selectedDatasetId: string;

  constructor(
    private route: ActivatedRoute
   ) { }

  ngOnInit() {
    this.route.parent.params.subscribe(
      (params: Params) => { 
        this.selectedDatasetId = params['dataset']
      }
     )
  }

}
