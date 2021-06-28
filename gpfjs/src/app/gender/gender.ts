import { Equals, ValidateIf } from 'class-validator';

export class Gender {
  male = true;
  female = true;

  @ValidateIf(o => !o.male && !o.female)
  @Equals(true, {
    message: 'select at least one'
  })
  unspecified = true;
}
