import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

export class Exon {
  constructor(
    public chrom: string,
    public start: number,
    public stop: number
  ) { }

  get length() {
    return this.stop - this.start;
  }

  public static fromJson(chrom: string, json: object): Exon {
    return new Exon(chrom, json['start'], json['stop']);
  }

  public static fromJsonArray(chrom: string, jsonArray: Array<Object>): Array<Exon> {
    return jsonArray.map(json => Exon.fromJson(chrom, json));
  }
}

export class Transcript {
  constructor(
    readonly transcript_id: string,
    readonly strand: string,
    readonly chrom: string,
    readonly cds: number[],
    readonly exons: Exon[]
  ) { }

  public static fromJson(json: object): Transcript {
    return new Transcript(
      json['transcript_id'], json['strand'], json['chrom'],
      json['cds'], Exon.fromJsonArray(json['chrom'], json['exons'])
    );
  }

  public static fromJsonArray(jsonArray: Array<Object>): Array<Transcript> {
    return jsonArray.map(json => Transcript.fromJson(json));
  }

  get start() {
    return this.exons[0].start;
  }

  get stop() {
    return this.exons[this.exons.length - 1].stop;
  }

  get length() {
    return this.stop - this.start;
  }

  get medianExonLength() {
    const middle: number = Math.floor(this.exons.length / 2);
    return this.exons[middle].length;
  }

  public isAreaInCDS(start: number, stop: number) {
    for (let i = 0; i < this.cds.length; i += 2) {
      if ((start >= this.cds[i]) && (stop <= this.cds[i + 1])) {
        return true;
      }
    }
    return false;
  }
}

export class Gene {
  constructor(
    readonly gene: string,
    readonly transcripts: Transcript[]
  ) { }

  public static fromJson(json: object): Gene {
    return new Gene(json['gene'], Transcript.fromJsonArray(json['transcripts']));
  }

  public static fromJsonArray(jsonArray: Array<Object>): Array<Gene> {
    return jsonArray.map(json => Gene.fromJson(json));
  }

  private mergeExons(exons: Exon[]): Exon[] {
    const sortedExons: Exon[] = exons.sort(
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
    return result;
  }

  public collapsedTranscript(): Transcript {
    const allExons: Exon[] = [];
    const cds: number[] = [];
    const codingSegments: Exon[] = [];
    let geneViewTranscript: GeneViewTranscript;

    for (const transcript of this.transcripts) {
      for (const exon of transcript.exons) {
        allExons.push(exon);
      }

      geneViewTranscript = new GeneViewTranscript(transcript);
      for (const segment of geneViewTranscript.segments) {
        if (segment.isCDS) {
          codingSegments.push(new Exon(segment.chrom, segment.start, segment.stop));
        }
      }
    }
    const result = this.mergeExons(allExons);
    const firstTranscript = this.transcripts[0];

    if (codingSegments.length === 0) {
      return new Transcript(
        'collapsed', firstTranscript.strand, firstTranscript.chrom, [], result
      );
    } else {
      // This is a hack to reuse the merging logic from exon merging, should eventually be reworked
      const cdsResult = this.mergeExons(codingSegments);
      cdsResult.forEach(element => cds.push(element.start, element.stop));

      return new Transcript(
        'collapsed', firstTranscript.strand, firstTranscript.chrom, cds, result
      );
    }
  }
}

export class GeneViewSummaryAllele {
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
  sauid: string;

  lgds = ['nonsense', 'splice-site', 'frame-shift', 'no-frame-shift-new-stop'];

  public static comparator(a: GeneViewSummaryAllele, b: GeneViewSummaryAllele) {
    if (a.comparisonValue > b.comparisonValue) {
      return 1;
    } else if (a.comparisonValue < b.comparisonValue) {
      return -1;
    } else {
      return 0;
    }
  }

  public static fromRow(row: any, svuid?: string): GeneViewSummaryAllele {
    const result = new GeneViewSummaryAllele();
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
    result.sauid = result.location + ':' + result.variant;
    result.svuid = svuid ? svuid : result.sauid;
    return result;
  }

  public isLGDs(): boolean {
    return (this.lgds.indexOf(this.effect) !== -1 || this.effect === 'lgds');
  }

  public isMissense(): boolean {
    return (this.effect === 'missense');
  }

  public isSynonymous(): boolean {
    return (this.effect === 'synonymous');
  }

  public isCNVPlus(): boolean {
    return (this.effect === 'CNV+');
  }

  public isCNVPMinus(): boolean {
    return (this.effect === 'CNV-');
  }

  public isCNV(): boolean {
    return this.isCNVPlus() || this.isCNVPMinus();
  }

  get comparisonValue(): number {
    let sum = 0;
    sum += this.seenAsDenovo && !this.isCNV() ? 200 : 100;
    sum += this.isLGDs() ? 50 : this.isMissense() ? 40 : this.isSynonymous() ? 30 : !this.isCNV() ? 20 : this.seenAsDenovo ? 10 : 5;
    sum += (this.seenInAffected && this.seenInUnaffected) ? 1 : this.seenInUnaffected ? 2 : 3;
    return sum;
  }

  public intersects(allele: GeneViewSummaryAllele): boolean {
    if (!this.isCNV()) {
      this.endPosition = this.position;
    }

    if (!allele.isCNV()) {
      allele.endPosition = allele.position;
    }

    return !(this.position >= allele.endPosition || this.endPosition <= allele.position);
  }
}

export class GeneViewSummaryAllelesArray {

  summaryAlleles: GeneViewSummaryAllele[] = [];
  summaryAlleleIds: string[] = [];

  addSummaryRow(row: any) {
    if (!row) {
      return;
    }
    for (let i = 0; i < row['alleles'].length; i++) {
      this.addSummaryAlleleRow(row['alleles'][i])
    }
  }

  addSummaryAllele(summaryAllele: GeneViewSummaryAllele) {
    const alleleIndex = this.summaryAlleleIds.indexOf(summaryAllele.sauid);
    if (alleleIndex !== -1) {
      this.summaryAlleles[alleleIndex].numberOfFamilyVariants =
        this.summaryAlleles[alleleIndex].numberOfFamilyVariants +
        summaryAllele.numberOfFamilyVariants;

      this.summaryAlleles[alleleIndex].seenAsDenovo =
        this.summaryAlleles[alleleIndex].seenAsDenovo || summaryAllele.seenAsDenovo;
      this.summaryAlleles[alleleIndex].seenInAffected =
        this.summaryAlleles[alleleIndex].seenInAffected || summaryAllele.seenInAffected;
      this.summaryAlleles[alleleIndex].seenInUnaffected =
        this.summaryAlleles[alleleIndex].seenInUnaffected || summaryAllele.seenInUnaffected;
    } else {
      this.summaryAlleles.push(summaryAllele);
      this.summaryAlleleIds.push(summaryAllele.sauid);
    }
  }

  addSummaryAlleleRow(alleleRow: any) {
    if (!alleleRow) {
      return;
    }
    const summaryAllele = GeneViewSummaryAllele.fromRow(alleleRow);
    this.addSummaryAllele(summaryAllele);
  }

  get totalFamilyVariantsCount(): number {
    return this.summaryAlleles.reduce((a, b) => a + b.numberOfFamilyVariants, 0);
  }

  get totalSummaryAllelesCount(): number {
    return this.summaryAlleles.length;
  }
}

export class DomainRange {
  constructor(
    public start: Number,
    public end: Number,
  ) {}
}

export class GeneViewTranscriptSegment {
  constructor(
    public chrom: string,
    public start: number,
    public stop: number,
    public isExon: boolean,
    public isCDS: boolean,
    public isSpacer: boolean,
    public label: string
  ) { }

  get length() {
    return (this.stop - this.start) * (this.isSpacer ? 2 : 1);
  }

  get isIntron() {
    return !this.isCDS;
  }

  intersectionLength(min: number, max: number): number {
    const start = Math.max(this.start, min);
    const stop = Math.min(this.stop, max);

    if (start >= stop) {
      return 0;
    } else {
      return stop - start;
    }
  }

  isSubSegment(min: number, max: number): boolean {
    return this.start >= min && this.stop <= max;
  }
}

export class GeneViewTranscript {
  transcript: Transcript;
  segments: GeneViewTranscriptSegment[] = [];
  chromosomes = {};

  get start() {
    return this.transcript.start;
  }

  get stop() {
    return this.transcript.stop;
  }

  get strand() {
    return this.transcript.strand;
  }

  constructor(transcript: Transcript) {
    this.transcript = transcript;

    const exonCount = this.transcript.exons.length;
    const intronCount = exonCount - 1;

    for (let i = 0; i < this.transcript.exons.length; i++) {
      this.segments.push(...this.exonToTranscriptSegments(this.transcript.exons[i], i, exonCount));
      if (i + 1 < this.transcript.exons.length) {
        // Add intron segment if applicable
        const spacer = this.transcript.exons[i].chrom !== this.transcript.exons[i + 1].chrom;
        this.segments.push(
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].chrom,
            this.transcript.exons[i].stop, this.transcript.exons[i + 1].start,
            false, false, spacer, `intron ${i + 1}/${intronCount}`)
        );
      }
    }
    // Calculate chromosomes (ignoring spacer introns)
    for (const segment of this.segments.filter(seg => !seg.isSpacer)) {
      if (!this.chromosomes.hasOwnProperty(segment.chrom)) {
        this.chromosomes[segment.chrom] = [segment.start, segment.stop];
      }
      this.chromosomes[segment.chrom][0] = Math.min(
        segment.start, this.chromosomes[segment.chrom][0]
      );
      this.chromosomes[segment.chrom][1] = Math.max(
        segment.stop, this.chromosomes[segment.chrom][1]
      );
    }
  }

  exonToTranscriptSegments(exon: Exon, exonIndex: number, exonCount: number): GeneViewTranscriptSegment[] {
    /*
      This method splits a single exon segment into multiple
      sub-segments at CDS transition points.
    */
    const result: GeneViewTranscriptSegment[] = [];
    const segmentTransitions = this.transcript.cds.filter(
      cdsTransitionPos => cdsTransitionPos >= exon.start && cdsTransitionPos <= exon.stop
    );
    if (segmentTransitions[segmentTransitions.length - 1] || segmentTransitions.length === 0) {
      segmentTransitions.push(exon.stop);
    }

    let posTracker = exon.start;
    segmentTransitions.forEach(transitionPos => {
      const isCDS = this.transcript.isAreaInCDS(posTracker, transitionPos);
      result.push(
        new GeneViewTranscriptSegment(
          exon.chrom, posTracker, transitionPos, true,
          isCDS, false, `exon ${exonIndex + 1}/${exonCount}`
        )
      );
      posTracker = transitionPos;
    });
    return result;
  }

  resolveRegionChromosomes(region: number[]): string[] {
    const regionMin = Math.min(...region);
    const regionMax = Math.max(...region);
    const result: string[] = [];
    for (const [chromosome, range] of Object.entries(this.chromosomes)) {
      if (range[0] >= regionMax || range[1] <= regionMin) {
        continue;
      } else {
        result.push(`${chromosome}:${Math.max(regionMin, range[0])}-${Math.min(regionMax, range[1])}`);
      }
    }
    return result;
  }
}
