import { GeneSetsCollection, GeneSet } from './gene-sets';

export const GENE_SETS_COLLECTION_CHANGE = 'GENE_SETS_COLLECTION_CHANGE';
export const GENE_SET_CHANGE = 'GENE_SET_CHANGE';


export interface GeneSetsState {
  geneSetsCollection: GeneSetsCollection;
  geneSetsTypes: Array<string>,
  geneSet: GeneSet;
};

const initialState: GeneSetsState = {
  geneSetsCollection: null,
  geneSetsTypes: [],
  geneSet: null
};

export function geneSetsReducer(
  state: GeneSetsState = initialState,
  action): GeneSetsState {


  switch (action.type) {
    case GENE_SETS_COLLECTION_CHANGE:
      return Object.assign({}, state,
        { geneSetsCollection: action.payload, geneSet: null });
    case GENE_SET_CHANGE:
      return Object.assign({}, state,
        { geneSet: action.payload });
    default:
      return state;
  }
};
