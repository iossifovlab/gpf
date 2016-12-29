import { Phenotype } from './phenotype';

export class Dataset {

  id: string;
  description: string;

  has_denovo: boolean;
  has_transmitted: boolean;
  has_cnv: boolean;

  phenotypes: Phenotype[];
}
