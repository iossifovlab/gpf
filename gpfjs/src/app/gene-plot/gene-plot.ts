import { Gene } from 'app/gene-browser/gene';

export class GenePlotModel {
  // TODO: This class can be reduced to two functions - buildDomain and buildRange
  public readonly gene: Gene;
  public readonly domain: number[];
  public readonly normalRange: number[];
  public readonly condensedRange: number[];
  public readonly spacerLength: number;

  constructor(gene: Gene, rangeWidth: number, spacerLength: number = 150) {
    this.gene = gene;
    this.spacerLength = spacerLength - (gene.transcripts.length >= 25 ? (gene.transcripts.length <= 50 ? gene.transcripts.length : 50) * 2.5 : 0); // in px
    // TODO: Could use positive and negative infinity here instead of magic numbers
    this.domain = this.buildDomain(0, 3000000000);
    this.normalRange = this.buildRange(0, 3000000000, rangeWidth, false);
    this.condensedRange = this.buildRange(0, 3000000000, rangeWidth, true);
  }

  public buildDomain(domainMin: number, domainMax: number) {
    const lastSegment = this.gene.collapsedTranscript.segments[this.gene.collapsedTranscript.segments.length - 1];
    return this.gene.collapsedTranscript.segments
      .filter(seg => seg.intersectionLength(domainMin, domainMax) > 0)
      .map(seg => seg.intersection(domainMin, domainMax)[0])
      .concat(domainMax < lastSegment.stop ? domainMax : lastSegment.stop);
  }

  public buildRange(domainMin: number, domainMax: number, rangeWidth: number, condenseIntrons: boolean) {
    const range: number[] = [0];
    const medianExonLength: number = this.gene.collapsedTranscript.medianExonLength;
    const filteredSegments = this.gene.collapsedTranscript.segments.filter(
      seg => seg.intersectionLength(domainMin, domainMax) > 0
    );

    let condensedLength = 0;
    let spacerCount = 0;

    for (const segment of filteredSegments) {
      if (segment.isSpacer) {
        spacerCount += 1;
      } else if (segment.isIntron && condenseIntrons) {
        const ratio = segment.intersectionLength(domainMin, domainMax) / segment.length;
        condensedLength += medianExonLength * ratio;
      } else {
        condensedLength += segment.intersectionLength(domainMin, domainMax);
      }
    }

    const scaleFactor: number = (rangeWidth - (spacerCount * this.spacerLength)) / condensedLength;
    let rollingTracker = 0;

    for (const segment of filteredSegments) {
      if (segment.isSpacer) {
        rollingTracker += this.spacerLength;
      } else if (segment.isIntron && condenseIntrons) {
        const ratio = segment.intersectionLength(domainMin, domainMax) / segment.length;
        rollingTracker += medianExonLength * ratio * scaleFactor;
      } else {
        rollingTracker += segment.intersectionLength(domainMin, domainMax) * scaleFactor;
      }
      range.push(rollingTracker);
    }
    return range;
  }
}

export class GenePlotScaleState {
  constructor(
    public xDomain: number[],
    public xRange: number[],
    public yMin: number,
    public yMax: number,
    public condenseToggled: boolean,
  ) { }

  get xMin(): number {
    return this.xDomain[0];
  }

  get xMax(): number {
    return this.xDomain[this.xDomain.length - 1];
  }
}

export class GenePlotZoomHistory {
  private stateList: GenePlotScaleState[];
  private currentStateIdx: number;

  constructor(private defaultState: GenePlotScaleState) {
    this.reset();
  }

  get currentState(): GenePlotScaleState {
    return this.stateList[this.currentStateIdx];
  }

  get canGoForward() {
    return this.currentStateIdx < this.stateList.length - 1;
  }

  get canGoBackward() {
    return this.currentStateIdx > 0;
  }

  public reset(): void {
    this.stateList = [this.defaultState];
    this.currentStateIdx = 0;
  }

  public addStateToHistory(scale: GenePlotScaleState): void {
    if (this.currentStateIdx < this.stateList.length - 1) {
      // overwrite history
      this.stateList = this.stateList.slice(0, this.currentStateIdx + 1);
    }
    this.stateList.push(scale);
    this.currentStateIdx++;
  }

  public moveToPrevious(): void {
    if (this.canGoBackward) {
      this.currentStateIdx--;
    }
  }

  public moveToNext(): void {
    if (this.canGoForward) {
      this.currentStateIdx++;
    }
  }
}
