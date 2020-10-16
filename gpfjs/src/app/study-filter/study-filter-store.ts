import { ValidateNested } from 'class-validator';
import { IsNotEmpty } from 'class-validator';

export class StudyDescriptor {
    studyId: string;
    studyName: string;
}

export class StudyFilterState {
  @IsNotEmpty()
  study: StudyDescriptor;
}

export class StudyFiltersState {
  @ValidateNested({
    each: true
  })
  studyFiltersState: StudyFilterState[] = [];
}
