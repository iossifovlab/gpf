import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';
import { GeneViewTranscript } from './gene-view';

export class Exon {
  constructor(
    public chrom: string,
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

  static fromJson(chrom: string, json: any): Exon {
    return new Exon(chrom, json['start'], json['stop']);
  }

  static fromJsonArray(chrom: string, jsonArray: Array<Object>): Array<Exon> {
    return jsonArray.map(json => Exon.fromJson(chrom, json));
  }
}

export class Transcript {
  constructor(
    private _transcript_id: string,
    private _strand: string,
    private _chrom: string,
    private _cds: number[],
    private _exons: Exon[]
  ) { }

  static fromJson(json: any): Transcript {
    return new Transcript(
      json['transcript_id'], json['strand'], json['chrom'],
      json['cds'], Exon.fromJsonArray(json['chrom'], json['exons']));
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
    const cds: number[] = [];
    const codingStartsAndStops: number[] = [];
    let geneViewTranscript: GeneViewTranscript;

    for (const transcript of this.transcripts) {
      for (const exon of transcript.exons) {
        allExons.push(exon);
      }

      geneViewTranscript = new GeneViewTranscript(transcript);
      for (const segment of geneViewTranscript.segments) {
        if (segment.isCDS) {
          codingStartsAndStops.push(segment.start, segment.stop);
        }
      }
    }

    cds.push(Math.min(...codingStartsAndStops), Math.max(...codingStartsAndStops));

    const sortedExons: Exon[] = allExons.sort(
      (e1, e2) => e1.start > e2.start ? 1 : -1
    );
    const result: Exon[] = [];
    const first: Exon = sortedExons[0];

    result.push(new Exon(first.chrom, first.start, first.stop));

    for (let i = 1; i < sortedExons.length; i++) {
      const curr = sortedExons[i];
      const prev = result[result.length - 1];
      if (curr.start <= prev.stop) {
        if (curr.stop > prev.stop) {
          prev.stop = curr.stop;
        }
        continue;
      }
      result.push(new Exon(curr.chrom, curr.start, curr.stop));
    }
    const firstTranscript = this.transcripts[0];

    return new Transcript(
      'collapsed', firstTranscript.strand, firstTranscript.chrom, cds, result
    );
  }
}

export class GeneViewSummaryVariant {
  location: string;
  position: number;
  endPosition: number;
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

  static comparator(a: GeneViewSummaryVariant, b: GeneViewSummaryVariant) {
    if (a.comparisonValue > b.comparisonValue) {
      return 1;
    } else if (a.comparisonValue < b.comparisonValue) {
      return -1;
    } else {
      return 0;
    }
  }

  static fromRow(row: any): GeneViewSummaryVariant {
    const result = new GeneViewSummaryVariant();
    result.location = row.location;
    result.position = row.position;
    result.endPosition = row.end_position;
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
    return (this.lgds.indexOf(this.effect) !== -1 || this.effect === 'lgds');
  }

  isMissense(): boolean {
    return (this.effect === 'missense');
  }

  isSynonymous(): boolean {
    return (this.effect === 'synonymous');
  }

  isCNVPlus(): boolean {
    return (this.effect === 'CNV+');
  }

  isCNVPMinus(): boolean {
    return (this.effect === 'CNV-');
  }

  isCNV(): boolean {
    return this.isCNVPlus() || this.isCNVPMinus();
  }

  get comparisonValue(): number {
    let sum = 0;

    sum += this.seenAsDenovo ? 200 : 100;
    sum += this.isLGDs() ? 30 : this.isMissense() ? 20 : 10;
    sum += (this.seenInAffected && this.seenInUnaffected) ? 1 : this.seenInUnaffected ? 2 : 3;
    return sum;
  }
}

export class GeneViewSummaryVariantsArray {
  summaryVariants: GeneViewSummaryVariant[] = [];
  summaryVariantsIds: string[] = [];

  constructor() { }

  addSummaryRow(variant: any) {
    if (!variant) {
      return;
    }
    const summaryVariant = GeneViewSummaryVariant.fromRow(variant);

    // This is a temporary fix to merge duplicate variants
    // TODO: Remove when backend is fixed
    if (this.summaryVariantsIds.indexOf(summaryVariant.svuid) !== -1) {
      return;
    }

    this.summaryVariants.push(summaryVariant);
    this.summaryVariantsIds.push(summaryVariant.svuid);
  }

  push(variant: GeneViewSummaryVariant) {
    this.summaryVariants.push(variant);
    this.summaryVariantsIds.push(variant.svuid);
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
