export function difference<T>(setA: Set<T>, setB: Set<T>) {
  let result = new Set<T>();

  setA.forEach(element => {
    if (!setB.has(element)) {
      result.add(element);
    }
  });

  return result;
}

export function hasIntersection<T>(setA: Set<T>, setB: Set<T>) {
  return intersection(setA, setB).size !== 0;
}

export function intersection<T>(setA: Set<T>, setB: Set<T>) {
  let result = new Set<T>();

  setA.forEach(element => {
    if (setB.has(element)) {
      result.add(element);
    }
  });

  return result;
}

export function equal<T>(setA: Set<T>, setB: Set<T>) {
  if (setA.size !== setB.size) {
    return false;
  }
  for (let a of Array.from(setA)) {
    if (!setB.has(a)) {
      return false;
    }
  }
  return true;
}

export function isSubset<T>(setA: Set<T>, setB: Set<T>) {
  for (let a of Array.from(setA)) {
    if (!setB.has(a)) {
      return false;
    }
  }
  return true;
}
