import { Equals, ValidateIf } from 'class-validator';


export class StudyTypes {
  we = true;

  @ValidateIf(o => !o.we)
  @Equals(true, {
    message: 'select at least one'
  })
  tg = true;
};

