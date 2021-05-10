import { IsDefined } from 'class-validator';

export class GeneSymbols {
  @IsDefined()
  geneSymbols = '';
}
