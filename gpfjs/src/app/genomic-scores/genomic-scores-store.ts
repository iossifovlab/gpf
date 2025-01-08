import { ArrayNotEmpty, IsNotEmpty, IsNumber, ValidateIf } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

import { CategoricalHistogramView } from '../genomic-scores-block/genomic-scores-block';
import { GenomicScoreState } from 'app/genomic-scores-block/genomic-scores-block.state';
import { HistogramType } from 'app/gene-scores/gene-scores.state';
import { GeneScoresComponent } from 'app/gene-scores/gene-scores.component';

export class GenomicScoreLocalState implements GenomicScoreState {
  @IsNotEmpty() public score: string;

  @ValidateIf(o => o.rangeStart !== null)
  @IsNumber()
  @IsLessThanOrEqual('rangeEnd')
  @IsMoreThanOrEqual('domainMin')
  @IsLessThanOrEqual('domainMax')
  public rangeStart: number;


  @ValidateIf(o => o.rangeEnd !== null)
  @IsNumber()
  @IsMoreThanOrEqual('rangeStart')
  @IsMoreThanOrEqual('domainMin')
  @IsLessThanOrEqual('domainMax')
  public rangeEnd: number;

  public histogramType: HistogramType;

  @ValidateIf(
    (component: GeneScoresComponent) => component.isCategoricalHistogram(component.selectedGeneScore.histogram)
  )
  @ArrayNotEmpty({message: 'Please select at least one bar.'})
  public values: string[] = [];
  public categoricalView: CategoricalHistogramView;
}
