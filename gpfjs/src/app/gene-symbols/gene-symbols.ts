import { IsNotEmpty } from "class-validator";
export const GENE_SYMBOLS_CHANGE = 'GENE_SYMBOLS_CHANGE';
export const GENE_SYMBOLS_INIT = 'GENE_SYMBOLS_INIT';


export class GeneSymbolsState {
  @IsNotEmpty()
  geneSymbols: string;
};

const initialState: GeneSymbolsState = {
  geneSymbols: ''
};

export function geneSymbolsReducer(
  state: GeneSymbolsState = initialState,
  action): GeneSymbolsState {

  switch (action.type) {
    case GENE_SYMBOLS_CHANGE:
      return Object.assign({}, state,
        { geneSymbols: action.payload });
    case GENE_SYMBOLS_INIT:
      return initialState;
    default:
      return state;
  }
};
