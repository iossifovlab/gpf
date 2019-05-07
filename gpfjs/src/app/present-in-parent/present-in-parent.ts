export const RARITY_ULTRARARE = 'ultraRare';
export const RARITY_INTERVAL = 'interval';
export const RARITY_RARE = 'rare';
export const RARITY_ALL = 'all';

import { Equals, ValidateIf, Min, Max } from 'class-validator';
import { IsLessThanOrEqual } from '../utils/is-less-than-validator';
import { IsMoreThanOrEqual } from '../utils/is-more-than-validator';

export class PresentInParent {
  @ValidateIf(o => !o.fatherOnly && !o.motherFather && !o.neither)
  @Equals(true, {
    message: 'select at least one'
  })
  motherOnly = false;

  fatherOnly = false;
  motherFather = false;
  neither = true;

  @ValidateIf(o => !o.ultraRare)
  @Min(0)
  @Max(100)
  @IsLessThanOrEqual('rarityIntervalEnd')
  rarityIntervalStart = 0;


  @ValidateIf(o => !o.ultraRare)
  @Min(0)
  @Max(100)
  @IsMoreThanOrEqual('rarityIntervalEnd')
  rarityIntervalEnd = 100;

  rarityType = RARITY_ULTRARARE;

  ultraRare = true;
}
