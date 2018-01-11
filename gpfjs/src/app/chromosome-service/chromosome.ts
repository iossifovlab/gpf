export class ChromosomeBand {
  start: number;
  end: number;
  name: string;
  gieStain: string;

  constructor(start: number, end: number, name: string, gieStain: string) {
    this.start = start;
    this.end = end;
    this.name = name;
    this.gieStain = gieStain;
  }

  static fromJson(json: any): ChromosomeBand {
    return new ChromosomeBand(json['start'], json['end'], json['name'], json['gieStain']);
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<ChromosomeBand> {
    return jsonArray.map(json => ChromosomeBand.fromJson(json));
  }
}

export class Chromosome {
  id: string;
  bands: ChromosomeBand[];
  centromerePosition: number;

  constructor(id: string, bands: ChromosomeBand[]) {
    this.id = id;
    this.bands = bands;
    for (let band of this.bands) {
      if (band.gieStain === 'acen') {
        this.centromerePosition = band.end;
        break;
      }
    }
  }

  static fromJson(json: any): Chromosome {
    return new Chromosome(json['name'], ChromosomeBand.fromJsonArray(json['bands']));
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<Chromosome> {
    return jsonArray.map((json) => Chromosome.fromJson(json));
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
