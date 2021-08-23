import { Gene, GeneViewTranscript } from 'app/gene-view/gene';

export class GeneViewModel {

  public gene: Gene;
  public geneViewTranscripts: GeneViewTranscript[] = [];
  public collapsedGeneViewTranscript: GeneViewTranscript;

  // FIXME: See if these vars can be made readonly
  public domain: number[];
  public normalRange: number[];
  public condensedRange: number[];
  public spacerLength: number;

  constructor(gene: Gene, rangeWidth: number, spacerLength: number = 150) {
    this.gene = gene;
    this.spacerLength = spacerLength; // in px
    for (const transcript of gene.transcripts) {
      this.geneViewTranscripts.push(new GeneViewTranscript(transcript));
    }
    this.collapsedGeneViewTranscript = new GeneViewTranscript(gene.collapsedTranscript());
    this.calculateRanges(rangeWidth);
  }

  // FIXME: See if this can be made private or removed
  public calculateRanges(rangeWidth) {
    this.domain = this.buildDomain(0, 3000000000);
    this.normalRange = this.buildRange(0, 3000000000, rangeWidth, false);
    this.condensedRange = this.buildRange(0, 3000000000, rangeWidth, true);
  }

  // FIXME: See if this can be made private
  public buildNormalIntronsRange(domainMin: number, domainMax: number, rangeWidth: number) {
    return this.buildRange(domainMin, domainMax, rangeWidth, false);
  }

  // FIXME: See if this can be made private
  public buildCondensedIntronsRange(domainMin: number, domainMax: number, rangeWidth: number) {
    return this.buildRange(domainMin, domainMax, rangeWidth, true);
  }

  // FIXME: See if this can be made private
  public buildDomain(domainMin: number, domainMax: number) {
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

  public buildRange(domainMin: number, domainMax: number, rangeWidth: number, condenseIntrons: boolean) {
    const range: number[] = [];
    const transcript = this.collapsedGeneViewTranscript.transcript;
    const filteredSegments = this.collapsedGeneViewTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0);

    const medianExonLength: number = transcript.medianExonLength;
    let condensedLength = 0;

    let spacerCount = 0;

    for (const segment of filteredSegments) {
      if (segment.isSpacer) {
        spacerCount += 1;
      } else if (segment.isIntron && condenseIntrons) {
        const intronLength = segment.length;
        const intersectionLength = segment.intersectionLength(domainMin, domainMax);
        const factor = intersectionLength / intronLength;

        condensedLength += medianExonLength * factor;
      } else {
        const length = segment.intersectionLength(domainMin, domainMax);
        condensedLength += length;
      }
    }

    const scaleFactor: number = (rangeWidth - spacerCount * this.spacerLength) / condensedLength;

    let rollingTracker = 0;
    range.push(0);

    for (const segment of filteredSegments) {
      if (segment.isSpacer) {
        rollingTracker += this.spacerLength;
      } else if (segment.isIntron && condenseIntrons) {
        const intronLength = segment.length;
        const intersectionLength = segment.intersectionLength(domainMin, domainMax);
        const factor = intersectionLength / intronLength;

        rollingTracker += medianExonLength * scaleFactor * factor;
      }  else {
        rollingTracker += segment.intersectionLength(domainMin, domainMax) * scaleFactor;
      }
      range.push(rollingTracker);
    }
    return range;
  }
}
