import { Gene, Transcript, Exon } from 'app/gene-view/gene';


export class GeneViewTranscriptSegment {

  private _start: number;
  private _stop: number;
  private _isExon: boolean;
  private _isCDS: boolean;
  private _label: string;

  constructor(
    start: number,
    stop: number,
    isExon: boolean,
    isCDS: boolean,
    label: string
  ) {
    this._start = start;
    this._stop = stop;
    this._isExon = isExon;
    this._isCDS = isCDS;
    this._label = label;
  }

  get start() {
    return this._start;
  }

  get stop() {
    return this._stop;
  }

  get length() {
    return this.stop - this.start;
  }

  get isExon() {
    return this._isExon;
  }

  get isIntron() {
    return !this._isCDS;
  }

  get isCDS() {
    return this._isCDS;
  }

  get label() {
    return this._label;
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
            segmentStart, cdsTransition, true,
            this.isAreaInCDS(segmentStart, cdsTransition),
            `exon ${i + 1}/${exonCount}`),
          new GeneViewTranscriptSegment(
            cdsTransition, segmentStop, true,
            this.isAreaInCDS(cdsTransition, segmentStop),
            `exon ${i + 1}/${exonCount}`)
        );
      } else {
        this.segments.push(
          new GeneViewTranscriptSegment(
            segmentStart, segmentStop, true,
            this.isAreaInCDS(segmentStart, segmentStop),
            `exon ${i + 1}/${exonCount}`)
        );
      }
      // Add intron segment if applicable
      if (i + 1 < this.transcript.exons.length) {
        this.segments.push(
          new GeneViewTranscriptSegment(
            segmentStop, this.transcript.exons[i + 1].start,
            false, false, `intron ${i + 1}/${intronCount}`)
        );
      }
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

  condensedRange: number[];
  condensedDomain: number[];
  normalDomain: number[];

  constructor(gene: Gene, rangeWidth: number) {
    this.gene = gene;
    this.rangeWidth = rangeWidth;

    for (const transcript of gene.transcripts) {
      this.geneViewTranscripts.push(new GeneViewTranscript(transcript));
    }

    this.collapsedGeneViewTranscript = new GeneViewTranscript(gene.collapsedTranscript());

    this.normalDomain = [
      this.collapsedGeneViewTranscript.start,
      this.collapsedGeneViewTranscript.stop
    ];

    this.condensedDomain = this.buildCondensedIntronsDomain(0, 3000000000);
    this.condensedRange = this.buildCondesedIntronsRange(0, 3000000000, this.rangeWidth);

  }

  buildCondensedIntronsDomain(domainMin: number, domainMax: number) {
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

  buildCondesedIntronsRange(domainMin: number, domainMax: number, rangeWidth: number) {
    const range: number[] = [];
    const transcript = this.collapsedGeneViewTranscript.transcript;
    const filteredSegments = this.collapsedGeneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    const medianExonLength: number = transcript.medianExonLength;
    let condensedLength = 0;

    for (const segment of filteredSegments) {
      if (segment.isIntron) {
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
      if (segment.isIntron) {
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
