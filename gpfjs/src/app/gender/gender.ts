import { Equals, ValidateIf } from 'class-validator';

export class Gender {
  public male = false;
  public female = false;

  @ValidateIf(o => !o.male && !o.female)
  @Equals(true, {message: 'Select at least one.'})
  public unspecified = false;
}
