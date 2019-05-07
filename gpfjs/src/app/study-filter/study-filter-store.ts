import { ValidateNested } from 'class-validator';
import { IsNotEmpty } from 'class-validator';

export class StudyFilterState {
  @IsNotEmpty()
  studyName: string;
}

export class StudyFiltersState {
  @ValidateNested({
    each: true
  })
  studyFiltersState: StudyFilterState[] = [];
}
