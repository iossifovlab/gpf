import { Gene, Transcript, Exon } from 'app/gene-view/gene';


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
      const cdsTransition = this.getCDSTransitionPos(this.transcript.exons[i]);
      const segmentStart = this.transcript.exons[i].start;
      const segmentStop = this.transcript.exons[i].stop;
      if (cdsTransition) {
        // Split exons which are both inside and outside the coding region into two segments
        this.segments.push(
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].chrom,
            segmentStart, cdsTransition, true,
            this.isAreaInCDS(segmentStart, cdsTransition), false,
            `exon ${i + 1}/${exonCount}`),
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].chrom,
            cdsTransition, segmentStop, true,
            this.isAreaInCDS(cdsTransition, segmentStop), false,
            `exon ${i + 1}/${exonCount}`)
        );
      } else {
        this.segments.push(
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].chrom,
            segmentStart, segmentStop, true,
            this.isAreaInCDS(segmentStart, segmentStop), false,
            `exon ${i + 1}/${exonCount}`)
        );
      }
      // Add intron segment if applicable
      if (i + 1 < this.transcript.exons.length) {
        const spacer = this.transcript.exons[i].chrom !== this.transcript.exons[i + 1].chrom;
        this.segments.push(
          new GeneViewTranscriptSegment(
            this.transcript.exons[i].chrom,
            segmentStop, this.transcript.exons[i + 1].start,
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

  isAreaInCDS(start: number, stop: number) {
    return (start >= this.transcript.cds[0]) && (stop <= this.transcript.cds[1]);
  }

  getCDSTransitionPos(exon: Exon) {
    const startIsInCDS = this.isAreaInCDS(exon.start, exon.start);
    const stopIsInCDS = this.isAreaInCDS(exon.stop, exon.stop);
    if (startIsInCDS !== stopIsInCDS) {
      return startIsInCDS ? this.transcript.cds[1] : this.transcript.cds[0];
    } else {
      return null;
    }
  }
}


export class GeneViewModel {

  gene: Gene;
  rangeWidth: number;
  geneViewTranscripts: GeneViewTranscript[] = [];
  collapsedGeneViewTranscript: GeneViewTranscript;

  domain: number[];
  normalRange: number[];
  condensedRange: number[];

  constructor(gene: Gene, rangeWidth: number) {
    this.gene = gene;
    this.rangeWidth = rangeWidth;

    for (const transcript of gene.transcripts) {
      this.geneViewTranscripts.push(new GeneViewTranscript(transcript));
    }

    this.collapsedGeneViewTranscript = new GeneViewTranscript(gene.collapsedTranscript());

    this.domain = this.buildDomain(0, 3000000000);
    this.normalRange = this.buildRange(0, 3000000000, (seg) => seg.isSpacer);
    this.condensedRange = this.buildRange(0, 3000000000, (seg) => seg.isIntron || seg.isSpacer);
  }

  buildNormalIntronsRange(domainMin: number, domainMax: number) {
    return this.buildRange(domainMin, domainMax, (seg) => seg.isSpacer);
  }

  buildCondensedIntronsRange(domainMin: number, domainMax: number) {
    return this.buildRange(domainMin, domainMax, (seg) => seg.isIntron || seg.isSpacer);
  }

  buildDomain(domainMin: number, domainMax: number) {
    const domain: number[] = [];
    const filteredSegments = this.collapsedGeneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    const firstSegment = filteredSegments[0];
    if (firstSegment.isSubSegment(domainMin, domainMax)) {
      domain.push(firstSegment.start);
    } else {
      domain.push(domainMin);
    }
    for (let i = 1; i < filteredSegments.length; i++) {
      const segment = filteredSegments[i];
      domain.push(segment.start);
    }
    const lastSegment = filteredSegments[filteredSegments.length - 1];
    if (lastSegment.stop <= domainMax) {
      domain.push(lastSegment.stop);
    } else {
      domain.push(domainMax);
    }

    return domain;
  }

  buildRange(domainMin: number, domainMax: number, condenseCriteria: (seg: GeneViewTranscriptSegment) => boolean) {
    const range: number[] = [];
    const transcript = this.collapsedGeneViewTranscript.transcript;
    const filteredSegments = this.collapsedGeneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    const medianExonLength: number = transcript.medianExonLength;
    let condensedLength = 0;

    for (const segment of filteredSegments) {
      if (condenseCriteria(segment)) {
        const intronLength = segment.length;
        const intersectionLength = segment.intersectionLength(domainMin, domainMax);
        const factor = intersectionLength / intronLength;

        condensedLength += medianExonLength * factor;
      } else {
        const length = segment.intersectionLength(domainMin, domainMax);
        condensedLength += length;
      }
    }

    const scaleFactor: number = this.rangeWidth / condensedLength;

    let rollingTracker = 0;
    range.push(0);

    for (const segment of filteredSegments) {
      if (condenseCriteria(segment)) {
        const intronLength = segment.length;
        const intersectionLength = segment.intersectionLength(domainMin, domainMax);
        const factor = intersectionLength / intronLength;

        rollingTracker += medianExonLength * scaleFactor * factor;
      } else {
        rollingTracker += segment.intersectionLength(domainMin, domainMax) * scaleFactor;
      }
      range.push(rollingTracker);
    }
    return range;
  }
}
