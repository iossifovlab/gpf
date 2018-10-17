import { Component, AfterViewInit, ElementRef, ViewChild, Input } from '@angular/core';


import { PedigreeData } from '../genotype-preview-model/genotype-preview';
import {
  PerfectlyDrawablePedigreeService
} from '../perfectly-drawable-pedigree/perfectly-drawable-pedigree.service';

declare var vis: any;

@Component({
  selector: 'gpf-vis-pedigree-input',
  templateUrl: './vis-pedigree-input.component.html',
  styleUrls: ['./vis-pedigree-input.component.css'],
  providers: [PerfectlyDrawablePedigreeService]
})
export class VisPedigreeInputComponent implements AfterViewInit {
  @Input() family: PedigreeData[];
  @ViewChild('visualization') element: ElementRef;

  constructor(
    private perfectlyDrawablePedigreeService: PerfectlyDrawablePedigreeService
  ) { }

  ngAfterViewInit() {
    // console.log(this.family);
    let sandwichInstance = this.perfectlyDrawablePedigreeService
      .createSandwichInstance(this.family);
    let container = this.element.nativeElement;
    // console.log("vertices", sandwichInstance.vertices);
    // console.log("required", Array.from(sandwichInstance.required).map(e => e[0].toString() + ":" + e[1].toString()));
    // console.log("forbidden", Array.from(sandwichInstance.forbidden).map(e => e[0].toString() + ":" + e[1].toString()));

    let itemsData = [];
    for (let vertex of sandwichInstance.vertices) {
      itemsData.push({
        id: vertex.toString() + vertex.constructor.name,
        label: vertex.constructor.name + " (" + vertex.toString() + ")/" + Array.from(vertex.generationRanks()).join(",")
      });
    }
    let items = new vis.DataSet(itemsData);

    let edgesData = [];
    for (let edge of Array.from(sandwichInstance.required)) {
      edgesData.push({
        from: edge[0].toString() + edge[0].constructor.name,
        to: edge[1].toString() + edge[1].constructor.name,
        scaling: {
          min: 10,
          max: 30
        },
        color: {
          color: "#e23f4d"
        }
      });
    }
    for (let edge of Array.from(sandwichInstance.forbidden)) {
      edgesData.push({
        from: edge[0].toString() + edge[0].constructor.name,
        to: edge[1].toString() + edge[1].constructor.name,
        dashes: true,
        physics: false,
        color: {
          opacity: 0.4
        }
      });
    }
    let edges = new vis.DataSet(edgesData);

    let data = {
      nodes: items,
      edges: edges
    };

    let options = {};

    let network = new vis.Network(container, data, options);
  }

}
