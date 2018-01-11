import { IsNotEmpty } from 'class-validator';
import { ContinuousMeasure } from '../measures/measures';


export class PhenoToolMeasure {

    @IsNotEmpty()
    measure: ContinuousMeasure = null;

    normalizeBy: string[] = new Array<string>();
};
