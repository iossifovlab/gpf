import { IsNotEmpty } from 'class-validator';
import { ContinuousMeasure } from '../measures/measures';


export class PhenoToolMeasure {

    @IsNotEmpty()
    measure: ContinuousMeasure = null;

    normalizeBy: Regression[] = new Array<Regression>();
}

export class Regression {
    constructor(
      public display_name: string,
      public instrument_name: string,
      public measure_name: string,
    ) { }
}
