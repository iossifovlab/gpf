import { Equals, ValidateIf } from 'class-validator';

export class Gender {
  female = true;

  @ValidateIf(o => !o.female)
  @Equals(true, {
    message: 'select at least one'
  })
  male = true;
};
