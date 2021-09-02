import { GenotypePreview } from 'app/genotype-preview-model/genotype-preview';

interface Segment {
  chromosome: string;
  start: number;
  stop: number;
}

function mergeSegments(exons: Segment[]): Segment[] {
  const sortedExons: Segment[] = [...exons].sort(
    (e1, e2) => e1.start > e2.start ? 1 : -1
  );
  const result: Segment[] = [sortedExons[0]];

  for (let i = 1; i < sortedExons.length; i++) {
    const [prev, curr] = [result[result.length - 1], sortedExons[i]];
    if (curr.start <= prev.stop) {
      prev.stop = Math.max(prev.stop, curr.stop);
    } else {
      result.push(curr);
    }
  }
  return result;
}

function collapseTranscripts(transcripts: Transcript[]): Transcript {
  const allExons: Segment[] = [];
  const allCodingSequences: Segment[] = [];
  for (const transcript of transcripts) {
    allExons.push(...transcript.exons);
    allCodingSequences.push(...transcript.codingSequences);
  }
  return new Transcript(
    'collapsed', transcripts[0].strand, transcripts[0].chromosome,
    mergeSegments(allCodingSequences), mergeSegments(allExons)
  );
}

export class TranscriptSegment {
  public readonly length: number;

  constructor(
    public readonly chromosome: string,
    public readonly start: number,
    public readonly stop: number,
    public readonly isExon: boolean,
    public readonly isCDS: boolean,
    public readonly isSpacer: boolean,
    public readonly label: string,
  ) {
    this.length = (this.stop - this.start) * (this.isSpacer ? 2 : 1);
  }

  get isIntron() {
    return !this.isCDS;
  }

  public intersectionLength(min: number, max: number): number {
    const start = Math.max(this.start, min);
    const stop = Math.min(this.stop, max);
    return start < stop ? stop - start : 0;
  }

  public isSubSegment(min: number, max: number): boolean {
    return this.start >= min && this.stop <= max;
  }
}

export class Transcript {
  public readonly start: number;
  public readonly stop: number;
  public readonly length: number;
  public readonly medianExonLength: number;
  public readonly segments: TranscriptSegment[] = [];

  constructor(
    public readonly transcriptId: string,
    public readonly chromosome: string,
    public readonly strand: string,
    public readonly codingSequences: Segment[],
    public readonly exons: Segment[]
  ) {
    const medianExon = exons[Math.floor(exons.length / 2)];
    const intronCount = exons.length - 1;
    this.start = exons[0].start;
    this.stop = exons[exons.length - 1].stop;
    this.length = this.stop - this.start;
    this.medianExonLength = medianExon.stop - medianExon.start;

    for (let i = 0; i < exons.length; i++) {
      this.segments.push(...this.exonToTranscriptSegments(exons[i], i, exons.length));
      // Add intron segments between exons
      if (i + 1 < exons.length) {
        /* We permit instantiating a transcript with exons on different chromosomes
         * to allow visualisation of genes whose transcripts may be found on
         * different chromosomes. The space between two chromosomes is filled with an
         * imaginary "spacer" intron which is not drawn on the plot. */
        const spacer: boolean = exons[i].chromosome !== exons[i + 1].chromosome;
        this.segments.push(
          new TranscriptSegment(
            exons[i].chromosome, exons[i].stop, exons[i + 1].start,
            false, false, spacer, `intron ${i + 1}/${intronCount}`)
        );
      }
    }
  }

  public static fromJson(json: object): Transcript {
    return new Transcript(
      json['transcript_id'], json['chrom'], json['strand'],
      json['cds'].map(exon => ({chrom: json['cds'], ...exon})),
      json['exons'].map(exon => ({chrom: json['chrom'], ...exon}))
    );
  }

  public isAreaInCDS(start: number, stop: number): boolean {
    return this.codingSequences.some(cds => start >= cds.start && stop <= cds.stop);
  }

  private exonToTranscriptSegments(exon: Segment, exonIndex: number, exonCount: number): TranscriptSegment[] {
    /*
      This method splits a single exon segment into multiple sub-segments at CDS transition points.
    */
    const result: TranscriptSegment[] = [];
    const segmentTransitions = this.codingSequences.map(
      cds => [cds.start, cds.stop]
    ).reduce(
      (acc, val) => acc.concat(val), []
    ).filter(
      cdsTransitionPos => cdsTransitionPos >= exon.start && cdsTransitionPos <= exon.stop
    );

    if (segmentTransitions[segmentTransitions.length - 1] || segmentTransitions.length === 0) {
      segmentTransitions.push(exon.stop);
    }

    let posTracker = exon.start;
    segmentTransitions.forEach(transitionPos => {
      const isCDS = this.isAreaInCDS(posTracker, transitionPos);
      result.push(
        new TranscriptSegment(
          exon.chromosome, posTracker, transitionPos, true,
          isCDS, false, `exon ${exonIndex + 1}/${exonCount}`
        )
      );
      posTracker = transitionPos;
    });
    return result;
  }
}

export class Gene {
  public readonly collapsedTranscript: Transcript;
  public readonly chromosomes: Map<string, [number, number]>;

  constructor(
    public readonly geneSymbol: string,
    public readonly transcripts: Transcript[]
  ) {
    this.collapsedTranscript = collapseTranscripts(this.transcripts);

    this.chromosomes = new Map<string, [number, number]>();
    for (const transcript of this.transcripts) {
      if (!this.chromosomes.has(transcript.chromosome)) {
        this.chromosomes.set(transcript.chromosome, [transcript.start, transcript.stop]);
      } else {
        this.chromosomes.set(transcript.chromosome, [
          Math.min(transcript.start, this.chromosomes.get(transcript.chromosome)[0]),
          Math.max(transcript.stop, this.chromosomes.get(transcript.chromosome)[1])
        ]);
      }
    }
  }

  public static fromJson(json: object): Gene {
    return new Gene(json['gene'], json['transcripts'].map(t => Transcript.fromJson(t)));
  }

  public getRegionString(start: number, stop: number): string[] {
    const result: string[] = [];
    for (const [chromosome, range] of this.chromosomes) {
      if (range[0] >= stop || range[1] <= start) {
        continue;
      } else {
        result.push(`${chromosome}:${Math.max(start, range[0])}-${Math.min(stop, range[1])}`);
      }
    }
    return result;
  }
}
