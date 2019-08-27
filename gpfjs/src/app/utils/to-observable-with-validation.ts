
import {throwError as observableThrowError,  Observable } from 'rxjs';
import { ValidationError, validate } from 'class-validator';

export function toValidationObservable<T>(obj: T): Observable<T> {
  return Observable.fromPromise(validate(obj))
    .switchMap(errors => {
      if (errors.length === 0) {
        return Observable.of(obj);
      }
      return observableThrowError(errors);
    });
}


export function validationErrorsToStringArray(validationErrors: ValidationError[]): Array<string> | Array<Array<string>> {
  let errors: string[] | string[][];

  validationErrors.map(elem => {
    if (elem.constraints) {
      if (!errors) {
        errors = new Array<string>();
      }
      (errors as string[]).push(...getSingleError(elem));
    } else {
      if (!errors) {
        errors = new Array<Array<string>>();
      }
      (errors as string[][]).push(...getMultipleErrors(elem));
    }

  });

  return errors;
}

function getSingleError(elem) {
  const result = new Array<string>();

  for (const object in elem.constraints) {
    if (elem.constraints.hasOwnProperty(object)) {
      result.push(elem.constraints[object]);
    }
  }

  return result;
}

function getMultipleErrors(elem) {
  const result = new Array<Array<string>>();

  for (const elemOuter of elem.children) {
    const errors = new Array<string>();

    for (const elemInner of elemOuter.children) {
      errors.push(...getSingleError(elemInner));
    }

    result.push(errors);
  }

  return result;
}
