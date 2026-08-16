/* eslint-disable @typescript-eslint/no-explicit-any */

class DOMPointPolyfill {
  x: number;
  y: number;
  z: number;
  w: number;
  constructor(x = 0, y = 0, z = 0, w = 1) {
    this.x = x;
    this.y = y;
    this.z = z;
    this.w = w;
  }
}

class DOMMatrixPolyfill {
  m11 = 1;
  m12 = 0;
  m13 = 0;
  m14 = 0;
  m21 = 0;
  m22 = 1;
  m23 = 0;
  m24 = 0;
  m31 = 0;
  m32 = 0;
  m33 = 1;
  m34 = 0;
  m41 = 0;
  m42 = 0;
  m43 = 0;
  m44 = 1;

  constructor(init?: string | number[]) {
    if (Array.isArray(init)) {
      if (init.length === 6) {
        this.m11 = init[0];
        this.m12 = init[1];
        this.m21 = init[2];
        this.m22 = init[3];
        this.m41 = init[4];
        this.m42 = init[5];
      } else if (init.length === 16) {
        [
          this.m11,
          this.m12,
          this.m13,
          this.m14,
          this.m21,
          this.m22,
          this.m23,
          this.m24,
          this.m31,
          this.m32,
          this.m33,
          this.m34,
          this.m41,
          this.m42,
          this.m43,
          this.m44,
        ] = init;
      }
    }
  }

  get a() {
    return this.m11;
  }
  set a(v) {
    this.m11 = v;
  }
  get b() {
    return this.m12;
  }
  set b(v) {
    this.m12 = v;
  }
  get c() {
    return this.m21;
  }
  set c(v) {
    this.m21 = v;
  }
  get d() {
    return this.m22;
  }
  set d(v) {
    this.m22 = v;
  }
  get e() {
    return this.m41;
  }
  set e(v) {
    this.m41 = v;
  }
  get f() {
    return this.m42;
  }
  set f(v) {
    this.m42 = v;
  }

  get is2D() {
    return (
      this.m13 === 0 &&
      this.m14 === 0 &&
      this.m23 === 0 &&
      this.m24 === 0 &&
      this.m31 === 0 &&
      this.m32 === 0 &&
      this.m33 === 1 &&
      this.m34 === 0 &&
      this.m43 === 0 &&
      this.m44 === 1
    );
  }

  get isIdentity() {
    return (
      this.m11 === 1 &&
      this.m12 === 0 &&
      this.m13 === 0 &&
      this.m14 === 0 &&
      this.m21 === 0 &&
      this.m22 === 1 &&
      this.m23 === 0 &&
      this.m24 === 0 &&
      this.m31 === 0 &&
      this.m32 === 0 &&
      this.m33 === 1 &&
      this.m34 === 0 &&
      this.m41 === 0 &&
      this.m42 === 0 &&
      this.m43 === 0 &&
      this.m44 === 1
    );
  }

  multiplySelf(other: DOMMatrixPolyfill): this {
    const a = this;
    const b = other;
    const r11 = a.m11 * b.m11 + a.m12 * b.m21 + a.m13 * b.m31 + a.m14 * b.m41;
    const r12 = a.m11 * b.m12 + a.m12 * b.m22 + a.m13 * b.m32 + a.m14 * b.m42;
    const r13 = a.m11 * b.m13 + a.m12 * b.m23 + a.m13 * b.m33 + a.m14 * b.m43;
    const r14 = a.m11 * b.m14 + a.m12 * b.m24 + a.m13 * b.m34 + a.m14 * b.m44;
    const r21 = a.m21 * b.m11 + a.m22 * b.m21 + a.m23 * b.m31 + a.m24 * b.m41;
    const r22 = a.m21 * b.m12 + a.m22 * b.m22 + a.m23 * b.m32 + a.m24 * b.m42;
    const r23 = a.m21 * b.m13 + a.m22 * b.m23 + a.m23 * b.m33 + a.m24 * b.m43;
    const r24 = a.m21 * b.m14 + a.m22 * b.m24 + a.m23 * b.m34 + a.m24 * b.m44;
    const r31 = a.m31 * b.m11 + a.m32 * b.m21 + a.m33 * b.m31 + a.m34 * b.m41;
    const r32 = a.m31 * b.m12 + a.m32 * b.m22 + a.m33 * b.m32 + a.m34 * b.m42;
    const r33 = a.m31 * b.m13 + a.m32 * b.m23 + a.m33 * b.m33 + a.m34 * b.m43;
    const r34 = a.m31 * b.m14 + a.m32 * b.m24 + a.m33 * b.m34 + a.m34 * b.m44;
    const r41 = a.m41 * b.m11 + a.m42 * b.m21 + a.m43 * b.m31 + a.m44 * b.m41;
    const r42 = a.m41 * b.m12 + a.m42 * b.m22 + a.m43 * b.m32 + a.m44 * b.m42;
    const r43 = a.m41 * b.m13 + a.m42 * b.m23 + a.m43 * b.m33 + a.m44 * b.m43;
    const r44 = a.m41 * b.m14 + a.m42 * b.m24 + a.m43 * b.m34 + a.m44 * b.m44;
    this.m11 = r11; this.m12 = r12; this.m13 = r13; this.m14 = r14;
    this.m21 = r21; this.m22 = r22; this.m23 = r23; this.m24 = r24;
    this.m31 = r31; this.m32 = r32; this.m33 = r33; this.m34 = r34;
    this.m41 = r41; this.m42 = r42; this.m43 = r43; this.m44 = r44;
    return this;
  }

  preMultiplySelf(other: DOMMatrixPolyfill): this {
    const clone = new DOMMatrixPolyfill();
    Object.assign(clone, other);
    clone.multiplySelf(this);
    Object.assign(this, {
      m11: clone.m11, m12: clone.m12, m13: clone.m13, m14: clone.m14,
      m21: clone.m21, m22: clone.m22, m23: clone.m23, m24: clone.m24,
      m31: clone.m31, m32: clone.m32, m33: clone.m33, m34: clone.m34,
      m41: clone.m41, m42: clone.m42, m43: clone.m43, m44: clone.m44,
    });
    return this;
  }

  multiply(other: DOMMatrixPolyfill): DOMMatrixPolyfill {
    const result = DOMMatrixPolyfill.fromMatrix(this);
    return result.multiplySelf(other);
  }

  translateSelf(tx = 0, ty = 0, tz = 0): this {
    const t = new DOMMatrixPolyfill([1, 0, 0, 1, tx, ty]);
    if (tz !== 0) {
      t.m33 = 1;
      t.m43 = tz;
    }
    return this.multiplySelf(t);
  }

  translate(tx = 0, ty = 0, tz = 0): DOMMatrixPolyfill {
    const result = DOMMatrixPolyfill.fromMatrix(this);
    return result.translateSelf(tx, ty, tz);
  }

  scaleSelf(sx = 1, sy?: number): this {
    const _sy = sy ?? sx;
    const s = new DOMMatrixPolyfill([sx, 0, 0, _sy, 0, 0]);
    return this.multiplySelf(s);
  }

  scale(sx = 1, sy?: number): DOMMatrixPolyfill {
    const result = DOMMatrixPolyfill.fromMatrix(this);
    return result.scaleSelf(sx, sy);
  }

  invertSelf(): this {
    const det =
      this.m11 * this.m22 - this.m12 * this.m21;
    if (Math.abs(det) < 1e-10) {
      this.m11 = NaN; this.m12 = NaN; this.m13 = NaN; this.m14 = NaN;
      this.m21 = NaN; this.m22 = NaN; this.m23 = NaN; this.m24 = NaN;
      this.m31 = NaN; this.m32 = NaN; this.m33 = NaN; this.m34 = NaN;
      this.m41 = NaN; this.m42 = NaN; this.m43 = NaN; this.m44 = NaN;
      return this;
    }
    const invDet = 1 / det;
    const a = this.m22 * invDet;
    const b = -this.m12 * invDet;
    const c = -this.m21 * invDet;
    const d = this.m11 * invDet;
    const e = (this.m21 * this.m42 - this.m22 * this.m41) * invDet;
    const f = (this.m12 * this.m41 - this.m11 * this.m42) * invDet;
    this.m11 = a; this.m12 = b;
    this.m21 = c; this.m22 = d;
    this.m41 = e; this.m42 = f;
    return this;
  }

  inverse(): DOMMatrixPolyfill {
    const result = DOMMatrixPolyfill.fromMatrix(this);
    return result.invertSelf();
  }

  transformPoint(point?: { x?: number; y?: number; z?: number; w?: number }) {
    const x = point?.x ?? 0;
    const y = point?.y ?? 0;
    return new DOMPointPolyfill(
      this.m11 * x + this.m21 * y + this.m41,
      this.m12 * x + this.m22 * y + this.m42,
    );
  }

  toFloat64Array() {
    return new Float64Array([
      this.m11, this.m12, this.m13, this.m14,
      this.m21, this.m22, this.m23, this.m24,
      this.m31, this.m32, this.m33, this.m34,
      this.m41, this.m42, this.m43, this.m44,
    ]);
  }

  toString() {
    return this.is2D
      ? `matrix(${this.a}, ${this.b}, ${this.c}, ${this.d}, ${this.e}, ${this.f})`
      : `matrix3d(${this.toFloat64Array().join(", ")})`;
  }

  static fromMatrix(other: any): DOMMatrixPolyfill {
    const m = new DOMMatrixPolyfill();
    m.m11 = other.m11 ?? 1; m.m12 = other.m12 ?? 0;
    m.m13 = other.m13 ?? 0; m.m14 = other.m14 ?? 0;
    m.m21 = other.m21 ?? 0; m.m22 = other.m22 ?? 1;
    m.m23 = other.m23 ?? 0; m.m24 = other.m24 ?? 0;
    m.m31 = other.m31 ?? 0; m.m32 = other.m32 ?? 0;
    m.m33 = other.m33 ?? 1; m.m34 = other.m34 ?? 0;
    m.m41 = other.m41 ?? 0; m.m42 = other.m42 ?? 0;
    m.m43 = other.m43 ?? 0; m.m44 = other.m44 ?? 1;
    return m;
  }

  static fromFloat64Array(arr: Float64Array): DOMMatrixPolyfill {
    return new DOMMatrixPolyfill(Array.from(arr));
  }
}

export function installPolyfills() {
  if (typeof globalThis.DOMMatrix === "undefined") {
    (globalThis as any).DOMMatrix = DOMMatrixPolyfill;
  }
  if (typeof globalThis.DOMPoint === "undefined") {
    (globalThis as any).DOMPoint = DOMPointPolyfill;
  }
  if (typeof globalThis.Path2D === "undefined") {
    (globalThis as any).Path2D = class Path2D {
      addPath() {}
    };
  }
}
