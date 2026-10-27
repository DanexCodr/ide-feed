Some time ago I decided to dust off my fast generic function dispatch work for
ECL. But before merging that, I decided to optimize the table-based dispatch to
have a good measure of how much better or worse it is and that opened a whole
can of worms, including a new implementation of hash tables and hash functions.

I know, that's a new level of traversing absurdly nested rabbit holes. There are
two good outcomes of this:

1. Hash tables and generic function dispatch will be much faster soon
2. I got inspired to write another blog post pertaining to Common Lisp

Regarding the first point, here are a few bar graphs generated using polyclot, a
work-in-progress McCLIM tool for plotting data (less is better):

![cherry-picking.png](https://turtleware.eu/posts/sxhash-equalp-files/cherry-picking.png)

Figure 1: SLOT-ACCESS/READER - standard reader benchmark (work in progress).

![htable-mixbag.png](https://turtleware.eu/posts/sxhash-equalp-files/htable-mixbag.png)

Figure 2: HTABLE-MIXBAG - EQUALP benchmark with randomized keys.

![htable-setrem.png](https://turtleware.eu/posts/sxhash-equalp-files/htable-setrem.png)

Figure 3: HTABLE-SETREM - benchmark for interleaved insert and remove.

![htable-string.png](https://turtleware.eu/posts/sxhash-equalp-files/htable-string.png)

Figure 4: HTABLE-SMALL-STRING - EQUALP benchmark with short strings.

As for the second point, while working on hashing under various Common Lisp
predicates, I decided to bite the bullet and fix a few ugly parts of ECL. Most
notably consistent hashing of numbers under the predicate #'EQUALP. The topic is
interesting enough to deserve a separate note. In this post I'm assuming binary
floats (the float radix is two). This is the float representation used in ECL.

## 1. Hashing numbers - warmup

### 1.1. Recap: hash table tests and hash functions

A quick recap about Common Lisp and hash tables. The standard prescribes that
conforming implementations must allow specifying the hash table tests EQ, EQL,
EQUAL and EQUALP. The last test is interesting, because numbers with different
representations are considered to be EQUALP when they are =. For example:

```
(equalp 1 1.0)           ; -> T
(equalp 1/2 0.5)         ; -> T
(equalp 1/3 (float 1/3)) ; -> NIL
(equalp 42 #C(42.0 0.0)) ; -> T
```

It is worth noting, that hashing can be lossy, but it can't be inconsistent with
the test. In other words this is a conforming hash function under #'EQUALP:

```
;; (equalp 1 1.0)                        ; is true
;; (= (hash-equalp 1) (hash-equalp 1.0)) ; is true

(defun hash-equalp (x)
  (typecase x
    (real      42)
    (complex   (if (zerop (imagpart x))
                   (hash-equalp (realpart x))
                   13))
    (otherwise 15)))
```

While this function is not conforming, because there are objects that are the
same under the test and have different hashes:

```
;; (equalp 1 1.0)                        ; is true
;; (= (hash-equalp 1) (hash-equalp 1.0)) ; is false

(defun hash-equalp (x)
  (typecase x
    (rational  1337)
    (float     7117)
    (complex   (if (zerop (imagpart x))
                   (hash-equalp (realpart x))
                   13))
    (otherwise 15)))
```

In other words, when two objects are equal under the supplied test, they must
produce the same hash, but two objects having the same hash does not imply that
they are equal under the supplied test.

Naive hashes, while conforming, miss the point. A good hashing function tries to
produce different hashes for objects that are not equivalent under the predicate
with a good bit distribution to ensure good hash table performance.

### 1.2. Recap: the numeric tower and mathematical equivalence

Common Lisp has a full numeric tower:

![numeric-tower.png](https://turtleware.eu/posts/sxhash-equalp-files/numeric-tower.png)

Figure 5: Common Lisp numeric tower.

Note that when complex floats have specialized representation, then there may be
multiple subtypes specialized to single-float, double-float etc. Numbers are #'=
to each other when their value is mathematically the same, regardless of the
underlying representation. That's a wonderful quality when you do math :-).

This quality is not so wonderful, when you want to produce good hashes under the
predicate #'EQUALP (that boils down to #'= for numbers). We need to construct a
function that will produce the same hashes with good quality for equal objects.

The biggest hurdle comes from the gap between representations of RATIONAL and
FLOAT objects. Conventionally representations are

Fixnums, bignums and ratios are disjoint under #'=. That leaves us with
questions:

1. When are two complex numbers mathematically equal? This one is easy. Two complex numbers are equal when their real parts are equal and their imaginary parts are equal.
2. When are two floats mathematically equal? To resolve this question we can cast the float with smaller precision to the float with bigger one and compare bits. There is a gotcha in that -0.0 is not EQL to +0.0, but it is always = to it, so we should canonicalize zeros first.
3. When is an integer mathematically equal to a float? When the float has no fractional part and integers are equal.
4. When is a ratio equal by #'= to a float? This is the most interesting question. To answer it, we need to dive a bit deeper into float representation. Finite binary float values conceptually are represented as: `(* sign mantissa (expt 2 exponent))` This corresponds to *dyadic rationals*, that is rational numbers whose denominator is a power of two: `(/ n (expt 2 k))` In other words a float and a ratio may be equal only when the ratio is dyadic, otherwise the ratio value can't be represented as a binary float (this post assumes that we operate on binary floats - with radix=2).

That sums up the recap about mathematical equivalence and numeric tower in
Common Lisp.

### 1.3. Establishing the baseline

The easiest, yet useless, approach is to always return a hash `42`. It is
adequate because that is the canonical answer to the most important question.

The easy and useful approach relies on the observation that hashing is lossy.
All real numbers are coerced to a float precision and hashed. When the rational
number does not fit in the float precision, then we hash its approximation. We
need to remember to canonicalize -0.0 to +0.0 and to disable floating point
exceptions for cases like overflows and underflows.

```
#define hash_single_float(h,v) hash_float((h), (double)(v))
#define hash_double_float(h,v) hash_float((h), (double)(v))

static inline void
hash_float(cl_hashstate *h, double v)
{
  if (v==-0.0) v=0.0;
  hash_data(h, &v, sizeof(v));
}

static inline void
hash_long_float(cl_hashstate *h, long double v)
{
  ECL_WITHOUT_FPE_BEGIN {
    hash_float(h, (double)(v));
  } ECL_WITHOUT_FPE_END;
}

#define hash_fixnum(h,x) hash_float((h),(double)ecl_fixnum(x))
#define hash_bignum(h,x) hash_rational((h),(x))
#define hash_ratio(h,x)  hash_rational((h),(x))

static inline void
hash_rational(cl_hashstate *h, cl_object x)
{
  ECL_WITHOUT_FPE_BEGIN {
    double v = ecl_to_double(x);
    hash_float(h, v);
  } ECL_WITHOUT_FPE_END;
}
```

This model is conceptually obvious, very maintainable, reasonably fast, and
there are relatively few collisions under the usual workload. We pay for it in a
few ways:

1. Aesthetically it is not pleasing – crude even.
2. "Relatively few collisions" applies only to toy examples, once we start using bigger integers and more precise ratios, the problem starts to show. For example 260 and 260+1 hash identically and that matters for 64bit IDs and timestamps.
3. Performance-wise we drop the ball for integers and rationals – we convert numbers between formats even when we could hash only a chunk of memory.

This list is ranked by importance as I see it. The main reason I've kept digging
deeper is that it was not to my taste. Then we had impracticality for serious
workloads, finally microoptimizations. I believe that the general audience has
these priorities in a reversed order.

## 2. Hashing numbers - round one

A harder but more precise way to hash numbers under the predicate #'EQUALP is to
introduce canonicalization rules:

1. Integers are hashed as integers In the case of FIXNUM we hash its value (a word without the tag) and in the case of BIGNUM we hash the sign and its limbs.
2. Finite floats without the fractional part are hashed as integers Ensures INTEGER <-> FLOAT correspondence. We can't cast LONG-FLOAT to DOUBLE-FLOAT and then cast to integer, because we'd miss many BIGNUM values. Caveat: with this approach big floats may cons full bignums.
3. Floats that are not integers are cast to DOUBLE-FLOAT and hashed Ensures X-FLOAT <-> Y-FLOAT correspondence. This approach is lossy for long floats if they have more bits than double floats, but simplifies the implementations because long double has a few "loose" bits that may differ between numbers with the same value. NaNs and infinities are hashed like other doubles because infinities are exact and NaN is never #'= to anything.
4. Dyadic ratios are hashed as DOUBLE-FLOAT Ensures FLOAT <-> RATIO correspondence. For simplicity we don't try to determine whether RATIO is representable as DOUBLE-FLOAT – if it is too big or too small, it will be represented either as a 0 or as an infinity.
5. Other ratios are hashed as pairs We hash the numerator and denominator separately.
6. Complex floats with `(ZEROP (IMAGPART X))` are hashed as `(HASH (REALPART X))` Because `(= 3 #c(3.0 0.0))` we need to canonicalize `(complex float)` while rational complex numbers are canonicalized implicitly. Other complexes are hashed as pairs, that is we hash the real part and imaginary part separately.

This approach results in fewer collisions and is fairly straightforward. Here is
the pseudocode:

```
(defun hash-equalp-number (state number)
  (typecase number
    (fixnum  (hash-word state number))
    (bignum  (hash-data state (signum number) (limbs number)))
    (float   (if (and (finitep number) (is-integer-p number))
                 (hash-equalp-number state (rational number))
                 ;; INV -0.0 and +0.0 are hashed as integers.
                 (hash-data state (coerce number 'double-float))))
    (ratio   (if (dyadic-ratio-p number)
                 ;; INV may produce infinity or zero (that's fine)
                 ;; Disable float overflow and underflow traps.
                 (hash-data state (coerce number 'double-float))
                 (progn
                   (hash-equalp-number state (numerator number))
                   (hash-equalp-number state (denominator number)))))
    (complex (if (zerop (imagpart number))
                 (hash-equalp-number state (realpart number))
                 (progn
                   (hash-equalp-number state (realpart number))
                   (hash-equalp-number state (imagpart number)))))))
```

### 2.1. Implementation bites

My initial implementation cast all floats to integers. When I was comparing ECL
to other implementations I was wondering why we are so slow compared to others.
The key insight came after the realization that randomized keys in the form
(random 20.0) were collapsed to only 20 distinct hashes.

Fixing that and giving non-integer floats distinct hashes gave ECL the most
noticeable boost on the HTABLE-MIXBAG benchmark (included at the beginning) –
the new version is 100x faster than the old one.

While implementing a test suite that ensured that hashes for bignums, dyadic
ratios, and corresponding floats matched, I've discovered a non-obvious bug
pertaining to casting double floats to integers. The code looked like this:

```
if (d<=MOST_POSITIVE_FIXNUM && d>=MOST_NEGATIVE_FIXNUM) return to_fixnum(d);
else                                                    return to_bignum(d);
```

But the `MOST_POSITIVE_FIXNUM` value on x86-64 is 2<sup>61</sup>-1. In other words, to
represent this number exactly as a double, we need 61 significant bits. That's a
shame because double has 53 significant bits, so `MOST_POSITIVE_FIXNUM`, when
converted to double, rounds to 2<sup>61</sup> and that can't fit in a fixnum. After
promotion the incorrect code is equivalent to:

```
if (d<=(1LL<<61) && d>=MOST_NEGATIVE_FIXNUM) return to_fixnum(d);
else                                         return to_bignum(d);
```

Oops, double is accidentally cast to fixnum when it is 2<sup>61</sup>. That's clearly a
problem! After finding the issue, the solution is easy. We need to find an exact
double that is the boundary. Note that integers are implemented as two's
complement, so the most negative fixnum was alright in our case:

```
double limit = ldexp(1.0, ECL_FIXNUM_BITS-ECL_TAG_BITS-1);
if (d<limit && d>=-limit) return to_fixnum(d);
else                      return to_bignum(d);
```

This fix is correct, yet it revealed another bug. But that's a different story
to tell.

## 3. Hashing numbers - round two

The approach above is correct and nice, but has a few important flaws:

- we cons a lot for big integer floats (2KB/float in the worst case)
- there is a whole class of dyadic ratios that don't fit in long-float
- long floats lose precision after cast to double, notably very small and very big values collapse to 0 and infinity

After the initial implementation it bugged me enough that I've decided to come
up with a new hashing scheme for numbers under the predicate EQUALP. The rules
are also simpler (at least conceptually):

1. Dyadic rationals are hashed as tuples (sign, mantissa, exponent)
2. Other numbers are hashed depending on their type (they are disjoint)

The representation `[SIGN MANTISSA EXPONENT]` does not require us to convert
between types and it is very compact. Moreover it is very precise and doesn't
produce unnecessary collisions. On the other hand it requires extra work to
normalize tuples. Here is the pseudocode:

```
(defun hash-equalp-number (state number)
  (typecase number
    (integer
     (multiple-value-bind (s m e) (compute-integer-dyad number)
       (hash-dyad state s m e)))
    (float
     (multiple-value-bind (s m e) (compute-float-dyad number)
       (hash-dyad state s m e)))
    (ratio
     (if (dyadic-ratio-p number)
         (multiple-value-bind (s m e) (compute-ratio-dyad number)
           (hash-dyad state s m e))
         (progn
           (hash-datatype-tag state :ratio)
           (hash-equalp-number state (numerator number))
           (hash-equalp-number state (denominator number)))))
    (complex
     (if (zerop (imagpart number))
         (hash-equalp-number state (realpart number))
         (progn
           (hash-datatype-tag state :complex)
           (hash-equalp-number state (realpart number))
           (hash-equalp-number state (imagpart number)))))))
```

The implementation is a bit less straightforward because we now need to be able
to compute mantissa from numbers. A few words about normalization:

- sign is -1, 0 or +1 for finite numbers – that solves normalization of -0.0/+0.0
- mantissa must be a positive odd integer or zero – that unifies all mantissas
- exponent is also an integer, so the number is (* sign mantissa (expt 2 exp))
- to hash unique values (like infinities) we will abuse sign to fit extra values

Every integer is a dyadic rational, so our task is to normalize it so that the
mantissa is an odd number and adjust the exponent accordingly.

```
(defun compute-integer-dyad (number &optional (exp 0))
  (when (zerop number)
    (return-from compute-integer-dyad
      (values 0 0 0)))
  ;; In the real code use COUNT-TRAILING-ZEROS + ASH.
  ;; Loop division is to make the mechanism clear.
  (do ((sign (signum number))
       (mantissa (abs number) (ash mantissa -1))
       (exponent exp (1+ exponent)))
      ((oddp mantissa)
       (values sign mantissa exponent))))
```

The implementation for float is also straightforward thanks to the function
INTEGER-DECODE-FLOAT. We also need to normalize the signed zero:

```
(defun compute-float-dyad (number)
  (cond ((nan-p number)
         (return-from compute-float-dyad
           (values -2 0 0)))
        ((negative-infinity-p number)
         (return-from compute-float-dyad
           (values -3 0 0)))
        ((positive-infinity-p number)
         (return-from compute-float-dyad
           (values +3 0 0))))
  (multiple-value-bind (mantissa exponent sign)
      (integer-decode-float number)
    (compute-integer-dyad (* sign mantissa) exponent)))
```

For ratios we will reuse the function that we have not defined in the last
section to decide whether the ratio is dyadic and if it is – convert it to the
canonical form:

```
(defun dyadic-ratio-p (number)
  ;; A positive integer is a power of 2 only when exactly one bit is set.
  (= 1 (logcount (denominator number))))

(defun compute-ratio-dyad (number)
  (values (signum number)
          ;; Ratios are already normalized(!)
          (abs (numerator number))
          ;; den = 2^k, shift = k+1 -> exponent = -k
          (- (1- (integer-length (denominator number))))))
```

Mind that the functions above are deliberately simple to illustrate how they
should work. We have also used non-standard functions NAN-P and INFINITY-P that
depend on the implementations extensions (or internals).

This is the most satisfying moment in the post – we have found an elegant and
universal (in this domain) abstraction that avoids float-to-bignum conversion,
hashes unequal numbers differently, and is easy to understand. That's the high
point of this post and the reason I've dubbed it "heavenly delights". Alas, it
is time to come back to earth and improve its performance. That's where the
engineering lives.

### 3.1. Back to earth

We have an elegant conceptual model. The thing with elegant conceptual models is
that they need to be dirtied to make them fast. And that's what we are going to
do now: we will bastardize the clean abstraction and make it performant under
usual scenarios without sacrificing precision. We are now optimizing.

Simplifications that we can climb down to from our normalized representation
[sign, mantissa, exponent] model:

1. When mantissa or exponent exceeds LONG-FLOAT precision, don't normalize the number As noted earlier, aside from floats, numbers in Common Lisp are disjoint, for example, there are no integers and ratios that are EQUALP to each other. In that case we use the most convenient hashing scheme for the specified type.
2. Dyads representable as fixnums are hashed as a fixnum (a signed integer) This is an opportunistic optimization tailored for quick fixnum hashing. We already know how to correctly determine when a float can be reliably cast to fixnum and other numbers don't intersect with fixnums.
3. Dyadic ratios in range are cast to `long double` and hashed as LONG-FLOAT This way we ensure that ratios and floats that are #'= are hashed the same. This is similar to "Round one" approach, but we retain the maximal precision.
4. Integer floats and bignums in range are hashed in a dyadic form This step allows us to avoid coercing floats to bignums and is a big memory allocation save. A small cost for bignums is that we need to decide before hashing whether it is in the LONG-FLOAT precision range.
5. Long floats exceeding double float precision are hashed in a dyadic form By avoiding lossy casts to double, we reduce number of collisions. Most notably, very small and very big values are not collapsed to zero and infinity. Such floats are hashed in a dyadic form because x87 floats have additional padding bits that may differ between equal values, so we can't hash memory.

Another minor optimization: we fold the sign and the exponent into a single word
to have fewer hash state updates as `8*exponent+sign` (sign has maximum 2 bits).

Notice that this scheme is very similar to the "Round one" approach. In practice
it only differs in how we treat floats, bignums and ratios:

| object | round 1 | current variant | note |
| --- | --- | --- | --- |
| `integer float` | `fixnum` or `bignum` | `fixnum` or `tuple` | depends on range |
| `fractional float` | `dfloat` | `dfloat` or `lfloat` | depends on precision |
| `dyadic-ratio` | `dfloat` | `dfloat` or `lfloat` | depends on precision |
| `fixnum` | `fixnum` | `fixnum` | no change |
| `bignum` | `bignum` | `bignum` or `tuple` | depends on precision |

A few concrete examples should illustrate these simplifications. They do not try
to test precise limits and the set is not exhaustive.

I'm assuming that FIXNUM has 62 bits and LONG-FLOAT has 64-bit mantissa, 15-bit
exponent and 1-bit for sign – typical on x86 with GCC.

| ## | dyadic number | canonical representation | cast | note |
| --- | --- | --- | --- | --- |
| 0. | `(/ 1 (expt 2 (expt 2 15)))` | `(1 1 -32768)` | `ratio` | too small |
| 1. | `(/ 1 (expt 2 (expt 2 11)))` | `(1 1 -2048)` | `lfloat` |  |
| 2. | `3/8` | `(1 3 -3)` | `dfloat` |  |
| 3. | `42` | `(1 21 1)` | `fixnum` |  |
| 4. | `most-positive-fixnum` | `(1 most-positive-fixnum 0)` | `fixnum` |  |
| 5. | `most-negative-fixnum` | `(-1 1 61)` | `fixnum` |  |
| 6. | `(1+ most-positive-fixnum)` | `(1 1 61)` | `dyadic` |  |
| 7. | `(1- most-negative-fixnum)` | `(-1 2305843009213693953 0)` | `dyadic` |  |
| 8. | `(expt 2 32768)` | `(1 1 32768)` | `bignum` |  |
| 9. | `(/ (1+ (expt 2 40)) 2)` | `(1 (1+ (expt 2 40)) -1)` | `dfloat` |  |
| a. | `(/ (1+ (expt 2 53)) 2)` | `(1 (1+ (expt 2 53)) -1)` | `lfloat` |  |
| b. | `(/ (1+ (expt 2 64)) 2)` | `(1 (1+ (expt 2 64)) -1)` | `ratio` | too big |
| c. | `13.0` | `(1 13 0)` | `fixnum` |  |
| d. | `(expt 2.0 61)` | `(1 1 61)` | `dyadic` |  |
| e. | `(expt 2.0l0 16383)` | `(1 1 16383)` | `dyadic` |  |
| f. | `(expt 2.0l0 16384)` | `(3 0 0)` | `dfloat` | infinity |

Illustrative pseudocode:

```
;;; There is something to be said about conventions. Our dyadic representation
;;; treats the mantissa as an odd integer, but the C representation of floats
;;; treats the mantissa as a fraction [0.5, 1.0). In practice this means that
;;; exponents in our canonical representation must be recalculated, because:
;;;
;;;   our-mantissa === (shift-to-odd (ash float-mantissa +ldbl-mant-dig+))
;;;   our-min-exp  === (- +ldbl-min-exp+ +ldbl-mant-dig+)
;;;   our-max-exp  === (- +ldbl-max-exp+ (integer-length our-mantissa))
;;;
;;; Note that FLOAT-MANTISSA assumes a fraction, but in practice we can usually
;;; extract bits directly and skip the shift by interpreting it as significand.
(defun hash-dyadic-number (state number)
  (multiple-value-bind (sign mantissa exponent)
      (dyadic-representation number)
    (let* ((num-len (integer-length mantissa))
           (min-exp (- +ldbl-min-exp+ +ldbl-mant-dig+))
           (max-exp (- +ldbl-max-exp+ num-len)))
      (if (and (<= num-len +ldbl-mant-dig+)
               (<= min-exp exponent max-exp))
          (hash-dyad state sign mantissa exponent)
          (hash-type state number)))))
```

### 3.2. Gravel details

Without further ado, let's dig into the actual implementation. I'm going to show
only relevant parts of C code for brevity. If you are not interested in C code
and microoptimizations, then just skip this section and move to benchmarks. Here
is a TL;DR table (complexes are normalized and each part is hashed with a tag):

| type | hash as | why? |
| --- | --- | --- |
| `fixnum` | `fixnum` | performance |
| `bignum` | `bignum` / `dyadic` | performance / equivalence (`lfloat/dfloat`) |
| `ratio` | `ratio` / `lfloat` | performance / equivalence (`lfloat/dfloat`) |
| `dfloat` | `fixnum` / `dyadic` / `dfloat` | performance / equivalence / performance |
| `lfloat` | `dfloat` / `fixnum` / `dyadic` | performance / performance / correctness |

In two places we will hash integers that may be either fixnums or bignums:

- the mantissa in a dyadic form (long double mantissa is 64bit on x86-64)
- a ratio's numerator and denominator when the ratio is not a dyadic number

Hashing them is straightforward. Note that hashing the fixnum is always cheap –
we hash a single word.

```
static inline void
hash_fixnum_data(cl_hashstate *h, cl_object x) {
  hash_word(h, ecl_fixnum(x));
}

#define hash_fixnum(h,x) hash_fixnum_data(h,x)

static inline void
hash_bignum_data(cl_hashstate *h, cl_object x) {
  hash_word(h, ecl_bigsgn(x));
  hash_data(h,
            ECL_BIGNUM_LIMBS(x),
            ECL_BIGNUM_USIZE(x) * sizeof(ecl_limb_t));
}

static void
hash_integer(cl_hashstate *h, cl_object x)
{
  if (ECL_FIXNUMP(x)) {
    hash_fixnum_data(h, x);
  } else {
    hash_bignum_data(h, x);
  }
}
```

Previously we were concerned with consing. This is why we go an extra mile to
not allocate bignums unnecessarily when we hash a bignum in a dyadic form. We
operate on a scratch register that is a thread-local variable in ECL when we
extract a mantissa:

```
static inline void
hash_and_free_bignum_register(cl_hashstate *h, cl_object mantissa) {
  /* INV this function assumes that mantissa is already positive. The bignum may
     not be normalized to fixnum. We free the register after hashing. */
  if (ECL_BIGNUM_SIZE(mantissa) == 1) {
    ecl_limb_t y = ECL_BIGNUM_LIMBS(mantissa)[0];
    if (y <= MOST_POSITIVE_FIXNUM) {
      hash_word(h, y);
      goto DONE;
    }
  }
  hash_bignum_data(h, mantissa);
 DONE:
  _ecl_big_register_free(mantissa);
}

/* When hashing bignums we see whether they fit in LONG-FLOAT and only then we
   cast it to a dyadic form. Otherwise we directly hash limbs. */
static void
hash_bignum(cl_hashstate *h, cl_object x) {
  cl_fixnum length = _ecl_big_integer_length(x);
  cl_fixnum exponent = _ecl_big_ctz(x);
  if (length-exponent<=LDBL_MANT_DIG && length<=LDBL_MAX_EXP) {
    /* To avoid allocating fresh bignums by ABS and ASH we opencode this:
       cl_object mantissa = ecl_ash(ecl_abs(x), -exponent); */
    cl_object reg = _ecl_big_register2();
    cl_fixnum signum = ecl_bigsgn(x);
    if (signum<0) {
      _ecl_big_neg(reg, x);
      _ecl_big_div_2exp(reg, reg, exponent);
    }
    else {
      _ecl_big_div_2exp(reg, x, exponent);
    }
    hash_word(h, 8*exponent+signum);
    hash_and_free_bignum_register(h, reg);
  } else {
    hash_bignum_data(h, x);
  }
}
```

Hashing a ratio is also plain. When the ratio is dyadic and its precision does
not exceed `long double` then we coerce it to that type and hash it. Otherwise
we add the tag and hash both integers. We are careful to not allocate memory.

```
static void
hash_ratio(cl_hashstate *h, cl_object x) {
  /* When the ratio is dyadic and within long-float precision, then we cast it
     to long double for consistent hashes. Otherwise we hash ratio as is. */
  cl_object num = ecl_ratio_num(x);
  cl_object den = ecl_ratio_den(x);
  /* Ratio is dyadic when denominator is a power of two. To avoid bignum
     arithmetic we provide an optimized path for each subtype of integer.
     ecl_zerop(ecl_boole(ECL_BOOLAND, den, ecl_one_minus(den))); */
  bool dyadic_p;
  if (ECL_FIXNUMP(den)) {
    /* Denominator is always positive, so fixnump(x) -> fixnump(x-1) */
    cl_fixnum dfix = ecl_fixnum(den);
    dyadic_p = !(dfix & (dfix-1));
  } else {
    /* When bignum is a pow2, then integer_length == ctz+1 or (popcount==1) */
    dyadic_p = ((_ecl_big_ctz(den)+1) == _ecl_big_integer_length(den));
  }
  if (dyadic_p) {
    /* Normally we would call here
       cl_fixnum length = ecl_integer_length(ecl_abs(num));

       But! Numerator is normalized to an odd integer because denominator is a
       power of two. INTEGER-LENGTH returns different values for X and -X only
       when X is a power of two, and the only odd power of two is X=1.

       (INTEGER-LENGTH -1) == 0 and 0 <= LDBL_MANT_DIG
       (INTEGER-LENGTH +1) == 1 and 1 <= LDBL_MANT_DIG

       This is why we don't need to call ABS on the numerator. QED. */
    cl_fixnum length = (ECL_FIXNUMP(num)
                        ? ecl_integer_length(num)
                        : _ecl_big_integer_length(num));
    cl_fixnum exponent = -(ecl_integer_length(den)-1);
    if (length <= LDBL_MANT_DIG && exponent >= LDBL_MIN_EXP-LDBL_MANT_DIG) {
      /* Generic way to do this is: hash_long_float(h, ecl_to_long_double(x));
         that path recomputes mantissa and exponent from ratio using a generic
         arithmetic. We already have everything ready. */
      long double value = (ECL_FIXNUMP(num)
                           ? ecl_fixnum(num)
                           : _ecl_big_get_lf(num));
      value = ldexpl(value, exponent);
      hash_long_float(h, value);
      return;
    }
  }
  /* Fall-through. */
  hash_word(h, t_ratio);
  hash_integer(h, num);
  hash_integer(h, den);
}
```

Hashing floats is the most demanding part in this program:

1. DOUBLE-FLOAT: the first branch ensures the same hashes for fixnums, bignums, and integer float types, while the second branch ensures the same hashes for ratios and fractional float types.
2. LONG-FLOAT: the first branch checks whether we can cast to double without losing precision. The second branch ensures same hashes for fixnums. The third branch unconditionally hashes the value in a dyadic form.

Initially I've introduced functions `decode_lf` and `decode_df` that extracted
mantissa and exponent from the number, but benchmarks showed that these small
allocations dominate both time and consing for relevant profiles. This is why
I've fused decoding and hashing and operate on a preallocated register. That's
the difference between coming up first and coming up third on the benchmark.

Decoding and hashing `double` and `long double` in a dyadic form are practically
the same, so I'm going to show only `hash_lfloat` version. Both functions have a
fast path when the mantissa fits in `cl_index`, and a portable slow path when it
doesn't. Initially I've picked `unsigned long long`, but this type can't be
directly assigned to a bignum in GMP, so I've decided on a more robust type.

Functions `hash_dfloat` and `hash_lfloat` are identical except for
`DBL_MANT_DIG` -> `LDBL_MANT_DIG`, `ldexp` -> `ldexpl` and `frexp` ->
`frexpl`. Common Lisp, with its organic macros, could save us repetition and
expand a single macro twice, but C preprocessor macros get hairy fast, so it is
better to copy-paste the code:

```
/* INV value is guaranteed to be finite and != 0. */

#define DECODE_SIGNUM(value,signum) \
  do { if (signbit(value)) { signum=-1; value=-value; } } while(0)

/* ... hash_dfloat(cl_hashstate *h, double value) ... */

static inline void
hash_lfloat(cl_hashstate *h, long double value)
{
#if LDBL_MANT_DIG <= ECL_FIXNUM_BITS
  int ctz, exponent, signum=1;
  cl_index mantissa;
  DECODE_SIGNUM(value, signum);
  value = ldexpl(frexpl(value, &exponent), LDBL_MANT_DIG);
  exponent -= LDBL_MANT_DIG;
  mantissa = (cl_index)value;
  ctz = ecl_ctz(mantissa);
  exponent += ctz;
  mantissa >>= ctz;
  /* binary80 mantissa is 64 bits so it can falsify <= MOST_POSITIVE_FIXNUM. */
  if (mantissa <= MOST_POSITIVE_FIXNUM) {
    hash_word(h, 8*exponent+signum);
    hash_word(h, mantissa);
  } else {
    cl_object reg = _ecl_big_register2();
    _ecl_big_set_idx(reg, mantissa);
    hash_word(h, 8*exponent+signum);
    hash_bignum_data(h, reg);
    _ecl_big_register_free(reg);
  }
#else /* Happens for 128bit floats (i.e aarch64). */
  const int fixnum_bits = ECL_FIXNUM_BITS-ECL_TAG_BITS-1;
  int ctz=0, exponent, signum=1;
  cl_object mantissa = _ecl_big_register2();
  cl_fixnum helper, iterator;
  DECODE_SIGNUM(value, signum);
  value = frexpl(value, &exponent);
  _ecl_big_set_ui(mantissa, 0);
  for(iterator=0; iterator<LDBL_MANT_DIG && value; iterator+=fixnum_bits) {
    value = ldexpl(value, fixnum_bits);
    helper = (cl_fixnum)value;
    value -= helper;
    _ecl_big_mul_2exp(mantissa, mantissa, fixnum_bits);
    _ecl_big_add_ui(mantissa, mantissa, helper);
    /* When this chunk contains only 0s, then we extend trailing zeros by
       fixnum_bits (chunk's size). Otherwise we start counting again. */
    ctz = !helper ? ctz+fixnum_bits : ecl_ctz(helper);
  }
  /* ctz is a trailing 0 count for the whole mantissa. iterator denotes how many
     bits we have shifted the mantissa. */
  exponent += ctz - iterator;
  _ecl_big_div_2exp(mantissa, mantissa, ctz);
  hash_word(h, 8*exponent+signum);
  hash_and_free_bignum_register(h, mantissa);
#endif
}
#undef DECODE_SIGNUM
```

At last we can hash some floats. Hashing single floats is trivial (we cast them
to double float) while hashing a long float requires more work:

```
#define hash_single_float(h,v) hash_double_float((h),(double)(v))

static void
hash_double_float(cl_hashstate *h, double value) {
  if (isfinite(value) && (value==trunc(value))) {
    const double limit = ldexp(1.0, ECL_FIXNUM_BITS-ECL_TAG_BITS-1);
    if (value < limit && value >= -limit) {
      hash_word(h, (cl_fixnum)value);
      return;
    }
    hash_dfloat(h, value);
    return;
  }
  /* Fall-through. */
  hash_data(h, &value, sizeof(value));
}

/* We need to ensure, that when long double can be represented as double without
   loss of precision, that is value == (double)value, to hash it as double. */
static void
hash_long_float(cl_hashstate *h, long double value) {
  /* Hash as double. */
  if (!isfinite(value)
      || (fabsl(value) <= DBL_MAX && value==(double)value) ) {
    hash_double_float(h, (double)value);
    return;
  }
  /* Hash as fixnum. */
  {
    const long double limit = ldexpl(1.0L, ECL_FIXNUM_BITS-ECL_TAG_BITS-1);
    if ((value==truncl(value)) && (value < limit) && value >= -limit) {
      hash_word(h, (cl_fixnum)value);
      return;
    }
  }
  /* Hash as long double in dyadic form -- this is both for compatibility with
     bignums and to avoid hashing padding bits on x87. */
  hash_lfloat(h, value);
}
```

And.. that's all. Complex numbers are hashed the same – when the complex float
imaginary part is zero then we hash only the real part, otherwise we hash both
parts. Summing things up, here are the dominant costs of the procedure:

| type | decision cost | dyadic hash cost | normal hash cost |
| --- | --- | --- | --- |
| `fixnum` | (none) | same as for EQL | same as for EQL |
| `bignum` | (negligible) | `(ash (abs x) -exp)` | same as for EQL |
| `ratio` | (negligible) | `hash_long_float` | same as for EQL |
| `float` | (negligible) | `hash_{dfloat,lfloat}` | same as for EQL |

- bignum decision cost boils down to counting trailing zeros, the dyadic hash operates in a register and it doesn't cons
- ratio decision cost is optimized to not perform bignum arithmetic, so the decision cost is negligible and the main cost is in hashing long double
- float creates an integer from the mantissa – in most cases it is a fixnum, otherwise it operates on a bignum register and it doesn't cons either

This section might not have been the most pleasant read (a lot of C code), but I
hope that it gave you some insight into how optimizing ECL hot paths looks like.
Certainly it would be nice to have Common Lisp compiler that targets C! Oh…

## 4. Benchmarks - knockout

I initially planned to run ad hoc benchmarks and get over with it, but
I had too much fun writing up tests and coming up with interesting
benchmark profiles and fell into another rabbit hole. In this section
we'll compare ECL with itself (of course), but we will also discuss
other implementations. All charts measure either the time or the
allocated memory and they are normalized to the range [0,1]. Less is
always better.

First let's focus on tests. I've devised a few profiles for comparisons:

All benchmarks first generate 2<sup>16</sup> keys according to their profile and prefill
the hash table in the setup phase to avoid resizing. Only after that we run the
benchmark. Each profile has the same number of keys that are randomized during
setup. Each test is run 8 times to average results.

We measure both run time and consed bytes. The benchmark itself runs SETHASH and
GETHASH for each key in the collection, so the hash table implementation impacts
cross-implementation comparisons. On the bright side, it also reveals when there
are systematic collisions between hashes.

Here is an interesting story (relevant to these charts!). While analyzing data
I've noticed that "ECL-round2" unexpectedly conses for three profiles: :DYADIC,
:TYPICAL and :AVERAGE. I've felt very disappointed with these, because I went to
great lengths to avoid consing. The investigation revealed that if we don't
mix in these tests floats and rationals then consing is consistently zero. That
was the "aha!" moment - hash table allocates memory when it compares float and
rational keys! I'm keeping the figures as-is, but keep in mind that "ECL-round2"
hashing really doesn't cons; allocations come from the key comparison. I *could*
pull out my yak shaver and fix EQUALP too, but this descent stops being funny.

ECL variants are: "warmup", "round one" and "round two" that correspond to
approaches discussed earlier: cast everything to double, type-specific hashes,
and the final version where we exploit a dyadic canonical form. All tests are
performed using the new hash function (xxhash) and hash table (swiss).

Tested implementations are CCL, ECL, LispWorks and SBCL. There are caveats:

- I initially planned to include ABCL and CLASP too, but a smoke test revealed ABCL#763 and CLASP#1876. Both share the same flaw as ECL before changes described in this post, that is they don't hash numbers correctly under EQUALP. Benchmarking them would be beside the point.
- LispWorks performs badly on profiles with float numbers and other results are dwarfed by it, so I've excluded LW from some plots (but accounted for it in relevant analysis)
- CCL is the mirror image of LispWorks, and performs badly on profiles with rationals (and it is great with floats), so it is also skipped on some plots
- The :COLLIDE test does not apply to other implementations because they don't have LONG-FLOAT that is separate from DOUBLE-FLOAT - we use :TYPICAL instead

The smoke test:

```
(defvar *ht* (make-hash-table :test #'equalp))
(setf (gethash 1/4 *ht*) 42)
(unless (eql (gethash 0.25 *ht*) 42) ; a proper test should cover more pairs
  (format t "ERROR: 1/4 and 0.25 do not share the hash value under EQUALP.~%"))
```

All charts report either elapsed time or allocated memory aggregated for the
whole execution. Smaller is better. Test results are normalized to [0, 1]
relative to the slowest / most consing variant in each panel. "0.00" means
"below 0.005" of the maximum, not zero. All measurements were performed on
`X86-64 Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz`.

One of the hardest parts in analyzing data is to decide what we can remove
without simplifying the picture too much. Interpretations presented in this
section skip many benchmarks to present an understandable story.

If you are curious whether new ECL excels at complex floats (it does), or
whether it is true that small doubles and fixnums do not cons (they don't), then
you can dive straight into the [raw data](https://turtleware.eu/posts/sxhash-equalp-files/results.lisp) or, if you don't trust my numbers, then
you may inspect the of the [number generator](https://turtleware.eu/posts/sxhash-equalp-files/setup-number.lisp).

### 4.1. ECL vs ECL

First we will compare ECL variants developed in this post. The first chart shows
a benchmark for basic types:

![equalp-ecl-basic-types.png](https://turtleware.eu/posts/sxhash-equalp-files/equalp-ecl-basic-types.png)

Figure 6: (ECL-warmup ECL-round1 ECL-round2) x BASIC-TYPES x (TIME CONS).

A few interesting observations emerge from this chart:

1. Hashing doubles is fastest on "ECL-warmup", because this implementation is simplest for that particular profile. It also doesn't cons. "ECL-round1" is dominated by memory allocations for large double values that are bignums.
2. Hashing ratios has progressively better results with each round, both the time and consing.
3. Hashing bignums is a mirror image to hashing doubles, where "ECL-round1" excels at bignums, "ECL-warmup" must coerce bignums to doubles and memory allocation dominates its time. "ECL-round2" is as performant as "ECL-round1".
4. Fixnums on all variants are on a relatively fast path and don't need to cons at all.

Notice that "ECL-round2" is slower only when we hash specifically doubles.
Otherwise it is always tied or it is the fastest. It also doesn't cons.

It already looks good, but charts start to look even more interesting when we
start exploiting mixed data patterns:

![equalp-ecl-mixed-data.png](https://turtleware.eu/posts/sxhash-equalp-files/equalp-ecl-mixed-data.png)

Figure 7: (ECL-warmup ECL-round1 ECL-round2) x MIXED-DATA x (TIME CONS).

1. The "beyond" profile is a benchmark where we generate bignums and ratios that can't be represented as float, but have a shape that resembles floats - both have a mantissa that can be stored in a double and an exponent that doesn't fit in binary128 floats (the most precise float on ECL aarch64 and no tested Lisp has a wider float). And it shows. "ECL-warmup" takes the bait and collapses everything to double. That spikes both allocations and collisions. "ECL-round1" avoids part of that cost because bignums are hashed as is and they avoid collapsing to a single hash (double positive infinity). "ECL-round2" avoids both allocation and the collision traps and it is 400x faster (0.3s vs 125s) and doesn't cons while "ECL-warmup" conses 2GB.
2. The "collide" profile is similar, but numbers can be neatly represented as a long float (binary80) and not as a double float (binary64). That means in particular that both ratios and bignums must be hashed in a compatible manner to floats. Once again "ECL-round2" is very fast (600x faster! 0.2s vs 118s) and doesn't cons, while "ECL-warmup" conses 833MB. "ECL-round2" has much less collisions than "ECL-warmup" thanks to exact bignum hashing.
3. The "dyadic" profile mixes fixnums, double floats, bignums in double float range and dyadic ratios in double float range. This profile forces the need to bring all numbers to the same canonical representation and does not exhibit any systematic collisions. Since all here boils down to doubles, "ECL-warmup" conses less than "ECL-round1", yet "ECL-round2" is even better thanks to our optimizations. Little consing that is exhibited comes from comparing floats and bignums with EQUALP (not from hashing).
4. The "average" profile takes rational and float numbers at random. Here we can again see that "ECL-round1" was not a regression over "ECL-warmup" - it was a targeted optimization that tried to balance effort between different types of numbers. Still, "ECL-round2" wins clearly against both variants.

My takeaways here are that:

- specialized implementations are better for their particular data profile, notably "ECL-warmup" excels at doubles; "ECL-round1" ties "ECL-round2" at bignums and balances other types well
- "ECL-round1" approach optimizes for typical cases, but it is not very frugal with memory (to the point where allocations dominate the benchmark in doubles)
- "ECL-round2" also optimizes for typical cases but it is also austere with memory allocations and avoids hash collisions - that is responsible for two orders of magnitude faster and leaner implementation for adverse profiles

### 4.2. ECL vs the world

Comparing implementations between each other is inherently noisy. They don't
share the same hash table implementation and various unrelated operations on the
hashing and hash table path have different cost profiles. That said with a big
set of data we can clearly see some trends. Let's start with basic types:

![equalp-all-basic-types.png](https://turtleware.eu/posts/sxhash-equalp-files/equalp-all-basic-types.png)

Figure 8: (CCL ECL LispWorks SBCL) x BASIC-TYPES x  (TIME CONS).

LispWorks is excluded from the test involving floats because it is around 2500x
slower than CCL (96s vs 0.04s) and conses 66MB while other implementations don't
cons at all. In benchmarks involving rational numbers it is competitive. My
guess is that LispWorks calls RATIONALIZE on floats and that get costly fast.

CCL is another side of the same coin. It performs well for floats (around 1.7x
slower than ECL and SBCL), but it is much worse for rationals. The difference is
not that drastic but still much slower for bignums compared to LispWorks (0.18s
vs 0.03s). It is surprising but it allocates data even for FIXNUMs. It probably
calls FLOAT on all numbers before hashing.

SBCL heavily optimizes fixnums, bignums, and doubles – it is a leader on these
basic types and it doesn't cons. It drops a ball with ratios where it is slower
and conses 155MB (while ECL nor LispWorks don't allocate memory for ratios).

ECL never conses and wins for ratios, while for other basic types it is always
second. For BIGNUM SBCL pulls ahead, while for FIXNUM and DOUBLE it follows
closely.

![equalp-all-mixed-data.png](https://turtleware.eu/posts/sxhash-equalp-files/equalp-all-mixed-data.png)

Figure 9: (CCL ECL LispWorks SBCL) x MIXED-DATA x  (TIME CONS).

Results in these benchmarks are implicit from tests on basic types:

- BEYOND, DYADIC and AVERAGE involve floats, so LispWorks is too slow to include. SBCL is also underperforming on these tests, because these profiles contain ratios - the cost seems to be dominated by memory allocations.
- TYPICAL profile is manageable for all implementations, but both CCL and LispWorks underperform because both (small) floats and rationals are in the test set. CCL allocates much more memory than others. SBCL performs well, but is slower than ECL.
- In all these tests with mixed numbers ECL is the leader and allocates least (as noted earlier, hashing itself doesn't cons at all).

My takeaway is that each implementation could close the gap to the others if:

- LispWorks adds hashing specialization for floats
- CCL adds hashing specialization for rationals
- SBCL adds hashing specialization for ratios

This new approach of ECL is competitive with all implementations on each metric
and it is either the first or a close second with the biggest (around 1.5x) gap
to SBCL hashing bignums.

## 5. Summary

The main takeaway here is that every dyadic rational has one canonical form that
may be used to produce good hashes under the EQUALP predicate and that efficient
implementations take liberties with simplifications after absorbing the model.

It may look like we have abandoned the elegant dyadic model in the later phase,
but that's not true: we don't lose precision by lossy casting to double and all
numbers except equal ones are hashed differently (hashing differently does not
imply different hashes just like tossing a dice differently does not guarantee
different results).

Another interesting insight is that we can learn a lot about strategies used by
different implementations by merely benchmarking them with cleverly put number
selection profiles.

In practice EQUALP is not often used as a hash test, so while the numbers look
impressive, the new approach is not a game changer. That said, there is value in
hashing under EQUALP precisely because it coalesces different numbers. Usage may
follow when implementations are performant, while underperforming abstractions
will almost certainly be skipped.

That's about the hashing itself, but the post is not only about hashing. Note
how we have started with a simple baseline model, improved it and then refined
our understanding with an elegant conceptual model. We didn't stop there: we
turned it into an efficient implementation through the optimization and
validation loop. That's an engineering lesson worth remembering even if you
don't care much about heavenly delights of hashing numbers under EQUALP.

Uff, the summary was exhausting. For me, this was certainly a fun trip.  I've
recently learned a lot about hashing, hash tables, number equivalence,
micro-optimizations, benchmarking and diving too deep. Look forward to:

- a blogpost that discusses new hash table and generic function implementations
- the next release with all accumulated performance and conformance improvements

You may find the current progress in the ECL repository under branches `xxhash`,
`swiss-ht` and `improve-gf-cache`.

Happy Hackshing!

Daniel

PS If you liked this post or have some interesting insights, then [let's chat](mailto:daniel@turtleware.eu).

PPS If you'd like to see more rabbit hole investigations like this one, you can
support me on [Patreon](https://www.patreon.com/c/jackdaniel_kochmanski).

PPPS I'd like to thank Charlie McMackin for proofreading this text and providing
many valuable remarks.