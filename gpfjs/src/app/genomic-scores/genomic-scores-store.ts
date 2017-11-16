import { GenomicScoresHistogramData } from './genomic-scores';
import { IsNotEmpty, IsNumber, Min, Max, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class GenomicScoreState {
    @IsNotEmpty()
    histogramData: GenomicScoresHistogramData;

    @ValidateIf(o => o.rangeStart !== null)
    @IsNumber()
    @IsLessThanOrEqual('rangeEnd')
    @IsMoreThanOrEqual('domainMin')
    @IsLessThanOrEqual('domainMax')
    rangeStart: number;


    @ValidateIf(o => o.rangeEnd !== null)
    @IsNumber()
    @IsMoreThanOrEqual('rangeStart')
    @IsMoreThanOrEqual('domainMin')
    @IsLessThanOrEqual('domainMax')
    rangeEnd: number;

    metric: any;
    domainMin: any;
    domainMax: any;
    id: any;

    constructor() {
        this.histogramData = null;
        this.rangeStart = null;
        this.rangeEnd = null;
    }
};

export class GenomicScoresState {
    genomicScoresState: GenomicScoreState[] = [];
};


// export function genomicScoresReducer(
//     state: GenomicScoresState = null,
//     action
// ): GenomicScoresState {

//     switch (action.type) {
//     case GENOMIC_SCORES_RANGE_START_CHANGE: {
//         let index = action.payload[0]
//         let newScore = Object.assign({}, state.genomicScoresState[index],
//             { rangeStart: action.payload[1] })
//         let newStateScore = state.genomicScoresState.map((item, index) => {
//             if (index == action.payload[0]) {
//                 return newScore;
//             }
//             return item;
//         });
//         return Object.assign({}, state, { genomicScoresState: newStateScore });
//     }
//     case GENOMIC_SCORES_RANGE_END_CHANGE: {
//         let index = action.payload[0]
//         let newScore = Object.assign({}, state.genomicScoresState[index],
//             { rangeEnd: action.payload[1] })
//         let newStateScore = state.genomicScoresState.map((item, index) => {
//             if (index == action.payload[0]) {
//                 return newScore;
//             }
//             return item;
//         });
//         return Object.assign({}, state, { genomicScoresState: newStateScore });
//     }
//     case GENOMIC_SCORES_CHANGE: {
//         let newScore = {
//             metric: action.payload[1],
//             histogramData: action.payload[2],
//             rangeStart: null,
//             rangeEnd: null,
//             domainMin: action.payload[2].bins[0],
//             domainMax: action.payload[2].bins[action.payload[2].bins.length - 1]
//         };
//         let newStateScore = state.genomicScoresState.map((item, index) => {
//             if (index == action.payload[0]) {
//                 return newScore;
//             }
//             return item;
//         });
//         return Object.assign({}, state, { genomicScoresState: newStateScore });
//     }
//     case GENOMIC_SCORE_ADD: {
//         let scoreState = new GenomicScoreState();
//         scoreState.id = action.payload;
//         let newStateAdd = [...state.genomicScoresState, scoreState];
//         return Object.assign({}, state, { genomicScoresState: newStateAdd });
//     }
//     case GENOMIC_SCORE_REMOVE: {
//         let newStateRemove = state.genomicScoresState.filter( (item, index) => index !== action.payload);
//         return Object.assign({}, state, { genomicScoresState: newStateRemove });
//     }
//     case GENOMIC_SCORES_INIT:
//         return initialState;
//     default:
//         return state;
//   }
// };
