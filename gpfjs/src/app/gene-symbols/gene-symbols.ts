export const GENE_SYMBOLS_CHANGE = 'GENE_SYMBOLS_CHANGE';


export interface GeneSymbolsState {
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
    default:
      return state;
  }
};
