import { Equals, ValidateIf } from 'class-validator';

export class Gender {
  male = false;
  female = false;

  @ValidateIf(o => !o.male && !o.female)
  @Equals(true, {
    message: 'select at least one'
  })
  unspecified = false;
}
