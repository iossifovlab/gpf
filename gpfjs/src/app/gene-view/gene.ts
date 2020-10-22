export class Exon {
  constructor(
    private _start: number,
    private _stop: number
  ) { }

  get start() {
    return this._start;
  }

  get stop() {
    return this._stop;
  }

  set start(start: number) {
    this._start = start;
  }

  set stop(stop: number) {
    this._stop = stop;
  }

  get length() {
    return this._stop - this._start;
  }

  static fromJson(json: any): Exon {
    return new Exon(json['start'], json['stop']);
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<Exon> {
    return jsonArray.map(json => Exon.fromJson(json));
  }
}

export class Transcript {
  constructor(
    private transcript_id: string,
    private _strand: string,
    private _chrom: string,
    private utr3: Exon,
    private utr5: Exon,
    private _cds: number[],
    private _exons: Exon[]
  ) { }

  static fromJson(json: any): Transcript {
    return new Transcript(
      json['transcript_id'], json['strand'], json['chrom'],
      Exon.fromJson(json['utr3']), Exon.fromJson(json['utr5']),
      json['cds'],
      Exon.fromJsonArray(json['exons']));
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<Transcript> {
    return jsonArray.map(json => Transcript.fromJson(json));
  }

  get exons() {
    return this._exons;
  }

  get strand() {
    return this._strand;
  }

  get cds() {
    return this._cds;
  }

  get chrom() {
    return this._chrom;
  }

  get start() {
    return this._exons[0].start;
  }

  get stop() {
    return this._exons[this._exons.length - 1].stop;
  }

  get length() {
    return this.stop - this.start;
  }

  get medianExonLength() {
    let middle: number = Math.floor(this.exons.length / 2);
    return this.exons[middle].length;
  }
}

export class Gene {
  constructor(
    private _gene: string,
    private _transcripts: Transcript[]
  ) { }

  static fromJson(json: any): Gene {
    return new Gene(json['gene'], Transcript.fromJsonArray(json['transcripts']));
  }

  static fromJsonArray(jsonArray: Array<Object>): Array<Gene> {
    return jsonArray.map(json => Gene.fromJson(json));
  }

  get transcripts() {
    return this._transcripts;
  }

  get gene() {
    return this._gene;
  }

  collapsedTranscript(): Transcript {
    let allExons: Exon[] = [];
    for (let transcipt of this.transcripts) {
      for (let exon of transcipt.exons) {
        allExons.push(exon)
      }
    }
    let sortedExons: Exon[] = allExons.sort(
      (e1, e2) => e1.start > e2.start ? 1 : -1
    )
    let result: Exon[] = [];
    const first: Exon = sortedExons[0];

    result.push(new Exon(first.start, first.stop));

    for (let i = 1; i < sortedExons.length; i++) {
      let curr = sortedExons[i];
      let prev = result[result.length - 1];
      if (curr.start <= prev.stop) {
        if (curr.stop > prev.stop) {
          prev.stop = curr.stop;
        }
        continue;
      }
      result.push(new Exon(curr.start, curr.stop))
    }
    const firstTranscript = this.transcripts[0];

    const firstExon = result[0];
    const lastExon = result[result.length - 1];
    let cds: number[] = [];
    cds.push(firstExon.start);
    cds.push(lastExon.stop);

    return new Transcript(
      "collapsed", firstTranscript.strand, firstTranscript.chrom,
      null, null,
      cds, result);
  }
}
