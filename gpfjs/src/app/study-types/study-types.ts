import { Equals, ValidateIf } from 'class-validator';


export class StudyTypes {
  we = true;

  tg = true;

  @ValidateIf(o => !o.we && !o.tg)
  @Equals(true, {
    message: 'select at least one'
  })
  wg = true;
}
