export class ChromosomeBand {
  start: number;
  end: number;
  color: number;
}

export class Chromosome {
  id: string;
  bands: ChromosomeBand[];
  centromerePosition: number;

  constructor(id: string, bands: ChromosomeBand[]) {
    this.id = id;
    this.bands = bands;
    for (let band of this.bands) {
      if (band.color === 6) {
        this.centromerePosition = band.end;
        break;
      }
    }
  }

  length() {
    return this.bands[this.bands.length - 1].end;
  }

  leftWidth() {
    return this.centromerePosition;
  }

  rightWidth() {
    return this.length() - this.leftWidth();
  }
}
