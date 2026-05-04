export type HistogramType = 'continuous' | 'categorical';

export class NumberHistogram {
  public constructor(
    public readonly bars: number[],
    public readonly bins: number[],
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly rangeMin: number,
    public readonly rangeMax: number,
    public readonly logScaleX: boolean,
    public readonly logScaleY: boolean,
  ) {
    if (bins.length === (bars.length + 1)) {
      bars.push(0);
    }
  }
}

export class CategoricalHistogram {
  public constructor(
    public readonly values: {name: string, value: number}[],
    public readonly valueOrder: string[],
    public readonly largeValuesDesc: string,
    public readonly smallValuesDesc: string,
    public readonly logScaleY: boolean,
    public readonly labelRotation: number,
    public readonly displayedValuesCount: number = null,
    public readonly displayedValuesPercent: number = null,
  ) { }
}

export type CategoricalHistogramView = 'range selector' | 'click selector' | 'dropdown selector';
