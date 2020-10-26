import { GenotypePreviewVariantsArray, GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

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
    private _transcript_id: string,
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

  get transcript_id() {
    return this._transcript_id;
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
    const middle: number = Math.floor(this.exons.length / 2);
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
    const allExons: Exon[] = [];
    for (const transcipt of this.transcripts) {
      for (const exon of transcipt.exons) {
        allExons.push(exon);
      }
    }
    const sortedExons: Exon[] = allExons.sort(
      (e1, e2) => e1.start > e2.start ? 1 : -1
    );
    const result: Exon[] = [];
    const first: Exon = sortedExons[0];

    result.push(new Exon(first.start, first.stop));

    for (let i = 1; i < sortedExons.length; i++) {
      const curr = sortedExons[i];
      const prev = result[result.length - 1];
      if (curr.start <= prev.stop) {
        if (curr.stop > prev.stop) {
          prev.stop = curr.stop;
        }
        continue;
      }
      result.push(new Exon(curr.start, curr.stop));
    }
    const firstTranscript = this.transcripts[0];

    const firstExon = result[0];
    const lastExon = result[result.length - 1];
    const cds: number[] = [];
    cds.push(firstExon.start);
    cds.push(lastExon.stop);

    return new Transcript(
      'collapsed', firstTranscript.strand, firstTranscript.chrom,
      null, null,
      cds, result);
  }
}

export class GeneViewSummaryVariant {
  location: string;
  position: number;
  chrom: string;
  variant: string;
  effect: string;
  frequency: number;
  numberOfFamilyVariants: number;
  seenAsDenovo: boolean;

  seenInAffected: boolean;
  seenInUnaffected: boolean;
  svuid: string;

  lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  static fromRow(row: any): GeneViewSummaryVariant {
    const result = new GeneViewSummaryVariant();
    result.location = row.location;
    result.position = row.position;
    result.chrom = row.chrom;
    result.variant = row.variant;
    result.effect = row.effect;
    result.frequency = row.frequency;
    result.numberOfFamilyVariants = row.family_variants_count;
    result.seenAsDenovo = row.is_denovo;
    result.seenInAffected = row.seen_in_affected;
    result.seenInUnaffected = row.seen_in_unaffected;
    result.svuid = result.location + ':' + result.variant;

    return result;
  }

  static fromPreviewVariant(config, genotypePreview: GenotypePreview): GeneViewSummaryVariant {
    const result = new GeneViewSummaryVariant();
    const location = genotypePreview.get(config.locationColumn);
    result.location = location;
    result.position = Number(location.slice(location.indexOf(':') + 1));
    result.chrom = location.slice(0, location.indexOf(':'));

    let frequency: string = genotypePreview.data.get(config.frequencyColumn);
    if (frequency === '-') {
      frequency = '0.0';
    }
    result.frequency = Number(frequency);

    result.effect = genotypePreview.get(config.effectColumn).toLowerCase();
    result.variant = genotypePreview.get('variant.variant');

    result.numberOfFamilyVariants = 1;

    result.seenAsDenovo = false;
    if (genotypePreview.get('variant.is denovo')) {
      result.seenAsDenovo = true;
    }
    result.seenInAffected = false;
    result.seenInUnaffected = false;
    for (const pedigreeData of genotypePreview.get('genotype')) {
      if (pedigreeData.label > 0) {
        if (pedigreeData.color === '#ffffff') {
          result.seenInUnaffected = true;
        } else {
          result.seenInAffected = true;
        }
      }
    }

    result.svuid = result.location + ':' + result.variant;

    return result;
  }

  isLGDs(): boolean {
    if (this.lgds.indexOf(this.effect) !== -1 || this.effect === 'lgds') {
      return true;
    }
    return false;
  }

  isMissense(): boolean {
    if (this.effect === 'missense') {
      return true;
    }
    return false;
  }

  isSynonymous(): boolean {
    if (this.effect === 'synonymous') {
      return true;
    }
    return false;
  }
}

export class GeneViewSummaryVariantsArray {
  summaryVariants: GeneViewSummaryVariant[] = [];

  constructor() { }

  addSummaryRow(variant: any) {
    if (!variant) {
      return;
    }
    const summaryVariant = GeneViewSummaryVariant.fromRow(variant);
    this.summaryVariants.push(summaryVariant);
  }

  push(variant: GeneViewSummaryVariant) {
    this.summaryVariants.push(variant);
  }
}

export class DomainRange {
  start: Number;
  end: Number;

  constructor(start: Number, end: Number) {
    this.start = start;
    this.end = end;
  }
}
