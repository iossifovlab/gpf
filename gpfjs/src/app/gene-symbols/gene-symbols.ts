import { IsNotEmpty } from 'class-validator';

export class GeneSymbols {
  @IsNotEmpty()
  geneSymbols = '';
};
