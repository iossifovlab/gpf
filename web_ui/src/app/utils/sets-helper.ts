export function difference<T>(setA: Set<T>, setB: Set<T>): Set<T> {
  const result = new Set<T>();

  setA.forEach(element => {
    if (!setB.has(element)) {
      result.add(element);
    }
  });

  return result;
}

export function hasIntersection<T>(setA: Set<T>, setB: Set<T>): boolean {
  return intersection(setA, setB).size !== 0;
}

export function intersection<T>(setA: Set<T>, setB: Set<T>): Set<T> {
  const result = new Set<T>();

  setA.forEach(element => {
    if (setB.has(element)) {
      result.add(element);
    }
  });

  return result;
}

export function equal<T>(setA: Set<T>, setB: Set<T>): boolean {
  if (setA.size !== setB.size) {
    return false;
  }
  for (const a of Array.from(setA)) {
    if (!setB.has(a)) {
      return false;
    }
  }
  return true;
}

export function isSubset<T>(setA: Set<T>, setB: Set<T>): boolean {
  for (const a of Array.from(setA)) {
    if (!setB.has(a)) {
      return false;
    }
  }
  return true;
}
