import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'gpf-genotype-browser-meta-view',
  templateUrl: './genotype-browser-meta-view.component.html',
  styleUrls: ['./genotype-browser-meta-view.component.css']
})
export class GenotypeBrowserMetaViewComponent implements OnInit {

  readonly metaDatasetId = 'META';

  constructor() { }

  ngOnInit() {
  }

}
