import { Equals, ValidateIf } from 'class-validator';

export class Gender {
  female = true;

  male = true;

  @ValidateIf(o => !o.female && !o.male)
  @Equals(true, {
    message: 'select at least one'
  })
  unknown = true;
};
