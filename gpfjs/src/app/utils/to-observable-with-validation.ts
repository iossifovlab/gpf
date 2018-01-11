import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ValidationError, validate } from 'class-validator';

export function toValidationObservable<T>(obj: T): Observable<T> {
  return Observable.fromPromise(validate(obj))
    .switchMap(errors => {
      if (errors.length === 0) {
        return Observable.of(obj);
      }
      return Observable.throw(errors);
    });
};


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
  let result = new Array<string>();

  for (let object in elem.constraints) {
    if (elem.constraints.hasOwnProperty(object)) {
      result.push(elem.constraints[object]);
    }
  }

  return result;
}

function getMultipleErrors(elem) {
  let result = new Array<Array<string>>();

  for (let elemOuter of elem.children) {
    let errors = new Array<string>();

    for (let elemInner of elemOuter.children) {
      errors.push(...getSingleError(elemInner));
    }

    result.push(errors);
  }

  return result;
}
