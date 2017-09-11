import { Component, Input, OnInit } from '@angular/core';

import { Chromosome } from '../chromosome-service/chromosome';

interface ColorsMap {
  [id: number]: string;
}

const COLORS: ColorsMap = {
  1 : 'white',
  2 : '#E8E8E8',
  3 : '#E0E0E0',
  4 : '#D8D8D8', 
  5 : '#D0D0D0',
  6 : '#808080',
  7 : '#A0A0A0',
  8 : '#C7C7C7',
};

class ChromosomeBandComponent {
  x: number;
  width: number;
  height: number;
  color: string;
}

@Component({
  selector: 'gpf-chromosome',
  templateUrl: './chromosome.component.html',
  styleUrls: ['./chromosome.component.css']
})
export class ChromosomeComponent implements OnInit {

  @Input()
  chromosome: Chromosome;

  @Input()
  width: number;

  @Input()
  height: number;

  @Input()
  scale: number;

  @Input()
  centromerePosition: number;

  startingPoint: number;
  leftWidth: number;
  rightWidth: number;
  leftBands: ChromosomeBandComponent[] = [];
  rightBands: ChromosomeBandComponent[] = [];

  constructor() { }

  ngOnInit() {
    this.leftWidth = this.chromosome.leftWidth() * this.scale;
    this.rightWidth = this.chromosome.rightWidth() * this.scale;
    this.startingPoint = this.centromerePosition - this.leftWidth;

    for (let band of this.chromosome.bands) {
      let bandComponent: ChromosomeBandComponent = {
        x: this.startingPoint + band.start * this.scale,
        width: (band.end - band.start) * this.scale,
        height: this.height - 2,
        color: COLORS[band.color]
      };
      if (band.end <= this.chromosome.leftWidth()) {
        this.leftBands.push(bandComponent);
      } else {
        this.rightBands.push(bandComponent);
      }
    }
  }
}
