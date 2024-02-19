import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';

@Component({
  selector: 'gpf-genotype-browser-single-view',
  templateUrl: './genotype-browser-single-view.component.html'
})
export class GenotypeBrowserSingleViewComponent implements OnInit {
  public selectedDatasetId: string;

  public constructor(
    private route: ActivatedRoute
  ) { }

  public ngOnInit(): void {
    this.route.parent.params.subscribe(
      (params: Params) => {
        this.selectedDatasetId = params.dataset as string;
      }
    );
  }
}
