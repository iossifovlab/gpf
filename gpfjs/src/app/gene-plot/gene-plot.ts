import { Gene } from 'app/gene-browser/gene';

export class GenePlotModel {

  public readonly gene: Gene;
  public readonly domain: number[];
  public readonly normalRange: number[];
  public readonly condensedRange: number[];
  public readonly spacerLength: number;

  constructor(gene: Gene, rangeWidth: number, spacerLength: number = 150) {
    this.gene = gene;
    this.spacerLength = spacerLength; // in px
    this.domain = this.buildDomain(0, 3000000000);
    this.normalRange = this.buildRange(0, 3000000000, rangeWidth, false);
    this.condensedRange = this.buildRange(0, 3000000000, rangeWidth, true);
  }

  public buildDomain(domainMin: number, domainMax: number) {
    const domain: number[] = [];
    const filteredSegments = this.gene.collapsedTranscript.segments.filter(
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
    const transcript = this.gene.collapsedTranscript;
    const filteredSegments = this.gene.collapsedTranscript.segments.filter(
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
