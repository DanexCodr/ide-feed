> I will be using x86 naming throughout this post, but the concepts apply to other architectures too. Basic familiarity with SIMD and x86 assembly is assumed; [uops.info](https://uops.info) and Intel’s [intrinsics guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html) explain any instruction you don’t recognize.

A lot of SIMD code, particularly in the graphics programming space, use vec3/vec4 types all over the place. The issue is that this typically doesn’t scale beyond the SSE instruction set. In this post I want to share how you can “transpose” those vectors into lanes to scale your math operations beyond just those typical 4 component XMM registers, and have the efficiency scale up to 8 or 16 wide vectors (or maybe 32 wide vectors, if we ever get them).

To avoid the use of intrinsics, I’ll use Clang’s vector extensions ([`ext_vector_type`](https://clang.llvm.org/docs/LanguageExtensions.html#vectors-and-extended-vectors)) to represent the operations, since they’re easier to read and the logic can easily be reimplemented with intrinsics.

We’re going to look at a simple case on how to do N dot products at the same time (where N is the architecture’s SIMD width), and a typical CPU frustum culler as a more advanced example.

> Frustum culling should ideally be done on a GPU, but that’s beyond this article

All measurements below have been made on a Ryzen 7 5800 (Zen 3) CPU, with Clang 23.1.0 targeting Windows x64. The compile flags are `-std=c++20 -O3 -ffast-math`, along with `-march=x86-64-v3` (AVX2, FMA and BMI2) for the 8 lane code, and `-march=x86-64-v2` (SSE4.2) for the 4 lane equivalents, for anyone who wants to follow along. Every number is the best of 12 runs, and varies by about 2% from run to run. All of the code is [on Compiler Explorer](https://godbolt.org/clientstate/eNrtWm1v2zgS_isDL5q1EtvNixEYdpLDbncLHHDdFmixPiAJDFqmbKKyZIhUbCeX--03M6QkSnHStJsebu_OHxKJHA7nnQ_HvmtpqbVKE90aXt611Kw1POq0YpHMczGXrWErPDhodVo6zbOQXl-_hjfpTEKUZnDVeic-q2QOH__67hcIaViHIpZgUhDJFm5kaJBsrWZmcdXqXSW8eLlSSLJWZjGErjazc9zh-BC670-gG0VCm-5SmAV0u0Zkc2nON4PTyWm_uwq7a5XM0rXuLvVNCKs41yCRi8wAV2Thgii7SHlzAu0BoApSB5BmvG2D4hjafUdxlTDBWYiiqMRc_KjBbFdSd0BoGNsdYXPah5mMFC4A3HE5LPTI4NfNKk4zfFggfZKWSxZSzGSmr5Jck4mQ9cnxxMA5PY2K0RxfBjyaJ1rNEzmDcCGy2rxbVhI015_26_NxihP0Z0SqWTr0xAnSRHEqDEwmwphMTXMjJ5N2W27MxHpqQoq3T4IgGHkL-89d2G8sHDx34cAutI56uQ_z-7SQMBVahSA3YrmK5cvvcpVYLWepabOhRccafBrA3VUC-MmkybMERG8D-zDFvwf4vOXnLT_f8vMtWuH-AcO-Y9j_Bob8vObndcHcWUWLpezASmj2F0a1y1eNEYb850objF9IkyKkC7EmznmY6jHJ-Hv59rLqP73PS1tFmywPDeAm_b9RYSh48habkfey9V9u_RdmxpHMr-S_ECurx3WPpH4w9tIaDJoaDHwNBr4GA1-DQV2DQV2DwQ4NBi-qwXfI_7dZrk2-hDCPY4zzHvyEJwfKDEqDYK8NYbO9BY2hZYs7FvFsKeIOrP3BNIq0NMxScIWtKHuos85jgzU_jWeUMVhylIEVHgrTdNMBXAjrhUx4DY7Q3jdKq2kse9-jHLlA-Bl3qkLgBEKZYEaPvJGFiKNfN0byiVK6HTN4qm0q3zTdOplMcxUblUxkLJe4cK20nDB90KgviVA3EpbSLNLZEIzEgKFElmq-MBhAWULVRcyFolCSNzLbWs8Qi2maxpDmRquZ_ECDNuN5vog-VG-PrFmKSJCkjQcihHjwHI7w3xkM8N_BQUlS2YL3Rzpk0LOGwYCkl8omGJtE6y2lTwh7cAR_gaPeYQSIYOh_5yHJ8ZdJ-g2SisK6onhTEbQpEVn7HgZrx4kfoMh2cI2qHiKLmqKe2yIRaznyNrCP98U2jgzjRhZevEnVjLPmN_Jju0Aa-0WwF24gx-xbMbTnmn0yJo2UECZM88TUnVXOKesxhWowGT42vMYR4ZIGiZ2k1Xyd38ryWyG_U_zX4FUYtRZgVoPL1XXHSn6proMHqzh-SiGaVi1lzaT43Bi_rxm_erEGKwXXCxUxSIRXcNr3eDirXyp4jRPXSNJuDu3BP0s3tY8CODuz7FCNf0A14-T35kdlNNTyVwrcwXRdqlACD7G2xVuby1TL3JTLny4QAm0nASZOlUX1WLI83_C6_7qYsoI67IbwSSQh8S1zl6LL5m8RYa70BA9j6MGny3yo0tZ4BR6zyuhlZWCydU2rsqQUEl6c764d_yvB_tKQ442FGjC2ngGMhhTt3MMB5RBGvpxiwqSRDRZG3IQa-B5dQO_vAg1-UBHeY_EY_-n3vx9PJlcJu0RuVlnlljHae4Bm-kGixx-l6DNFMlNRdc1kbcbPvfaN_fsish7byzHv8DVLKY3HfJRjOj9v4RVmHV4GhZFwRuMJ3oXg04WPoU9qGPoTII7bdhgs3z_F4FMdM1suZ58u6rDZG_72W9IjEvjsIcxSrf-QOHelELdYgwoh0BTF44aHrcy3nfJxy8NbR3L_BaGd3fkorhm-pk2BzLEK_saPo8I7rIrwcOzT--BhcvL4NrYod-rw2NJhRr7HRHVAVNMWBnsuqcX2UbwtBMLO1TuVfOSWzC-u0nogNnDGv2sWR0anCUazh_YEvlLhT4JajWT3JGxuK7Hnikr03qZRsw9wzbZaU_nJW7Pdsea2WlNFgrfm9sEah01HDbD5iA0FdcyoJhq1lE-a0VqqihUO3NUOkzob8QHcK4LHHbnuQF31ymDyHc4HaM-LquLMKPpUP2epmIXYrcQmpAgXuPdyhSUcbw2owQ3VsRQUTqbrqpni56YtlRdW_UcuW3euoLZvehs858uXrf9yG1TJRchNkkh8BY3T8DNJU55D7q5FtzCtNg4g0I24uBB3jwgZkNj1W2oHDmkiSU1vZ2Z9wMziAu7o3wn9uV3CtrrGe1awovp8KHBeqbzPyJ4I43b3qAj9r8FkBZO9c7tnb2c0lTgpcJeoytueLxwvz9LjTBnXHLDghC791vRsTzwABcdyD95i24o7t4gL0JhTGYpcS3hDbXZIqYVN12jmSpshHjA2ggRw80vZ8hKn6Yo2RM60XBGucDdnq99Vcnk5T_LhUMRrsdUTu-H1tdsZGIevSW52yS4A7lvfA9qRyrR5JvBm7dkv_HSGAbi3ZzlgVrkxB8npreG1BkgkGO-vHe2i5B74QsYzJHbCXxIx4cSjPwws2xagBhZb8jb-6ENE-VhoROjQCNGhy80SGOLXEpRtsTIGw5VAlUiwMqbcRlK4zoYGsiuVFVkmtrTIkryCAbGfbjEvSZNBz9262Ns_03Zf6-3SKdbMFmWxHudeGwgnMQCNxVjtkhVTByNX7v2OmG3x0IT78mPPSn2OUimqzCvMuAlV1jNHsH9ROCm4tJGA-l2XRzIWpgqithEIInqtX_Ms-0pmFIU3aLsNOqxWKS13_apelfMuEBp-Ik6Ly4yV8BV1nrwPuW-dWr9zIET4hRquEbQTS7iL8aCK6i9Kj4F7uHk7eqB2m_9TVON045pUhPJjNyMnrm1ruual5NvKPEvzFSsy7vB3ebZAoVh2Cr9XmM0IGOWGvg10R1CtF_BoCXqyB1A_TPadiM-sTNY3XJrsY1mHXIU5h3EtdLxaWYrnn3F29zIqx9g8cqdZpyiZVp6GbT3sUgMCzV7nQ0Rg8UIJDgMHoKrGAI9WAMFhMA8k1B3wkVa_p3PwC56IbCP9212xQ2d39J5eP_NwrxxTHtpI41nOCUmHeVkf_kNDoO4GrtB8bHzvjNhhCc9OpRkwZc_On2Mae7Z8m2mC5tWA-lI1t-B-5RlCnceiyDgMyWgVT8HkR8MHK2aDUVi45ymWKUYa06134vz7_Fmm1fMd-6dNsP9H1PeIKPzRTeh-Y1L9NKcV0pXh-OToEKfTlbG_22k99TOa5k9jvvC7GuQbIc7gTe9aU5WIbNsacvOXBaLv_N6j4VpDapd3WjO5RIliWb6rDKEgfmOkixG5kSF240omBPLiYjIWU8RV5ZuaZrgf_cCoGMJe3tItvb_vvJAVjv_UVri-v77_FyMr4TU), with one pane for each instruction set.

> `-ffast-math` lets the compiler assume no value is NaN or infinite. If your bounding boxes can have NaN or infinite positions or sizes, don’t use the flag: the culler’s comparisons may then give any answer for those boxes.

## The basic example

Let’s take a look at what one dot product typically compiles to:

```
using vec3 = float __attribute__((ext_vector_type(3)));
using vec4 = float __attribute__((ext_vector_type(4)));
using vec8 = float __attribute__((ext_vector_type(8)));

float dot(vec3 a, vec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

float dot(vec4 a, vec4 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
```

```
using vec3 = float __attribute__((ext_vector_type(3)));
using vec4 = float __attribute__((ext_vector_type(4)));
using vec8 = float __attribute__((ext_vector_type(8)));

float dot(vec3 a, vec3 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

float dot(vec4 a, vec4 b) {
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
```

The assembly:

```
dot(float vector[3], float vector[3]):
    vmovaps    xmm0, xmmword ptr [rcx]
    vmulps     xmm0, xmm0, xmmword ptr [rdx]
    vmovshdup  xmm1, xmm0
    vaddss     xmm1, xmm0, xmm1
    vshufpd    xmm0, xmm0, xmm0, 1
    vaddss     xmm0, xmm1, xmm0
    ret

dot(float vector[4], float vector[4]):
    vmovaps    xmm0, xmmword ptr [rcx]
    vmulps     xmm0, xmm0, xmmword ptr [rdx]
    vshufpd    xmm1, xmm0, xmm0, 1
    vaddps     xmm0, xmm0, xmm1
    vmovshdup  xmm1, xmm0
    vaddss     xmm0, xmm0, xmm1
    ret
```

```
dot(float vector[3], float vector[3]):
    vmovaps    xmm0, xmmword ptr [rcx]
    vmulps     xmm0, xmm0, xmmword ptr [rdx]
    vmovshdup  xmm1, xmm0
    vaddss     xmm1, xmm0, xmm1
    vshufpd    xmm0, xmm0, xmm0, 1
    vaddss     xmm0, xmm1, xmm0
    ret

dot(float vector[4], float vector[4]):
    vmovaps    xmm0, xmmword ptr [rcx]
    vmulps     xmm0, xmm0, xmmword ptr [rdx]
    vshufpd    xmm1, xmm0, xmm0, 1
    vaddps     xmm0, xmm0, xmm1
    vmovshdup  xmm1, xmm0
    vaddss     xmm0, xmm0, xmm1
    ret
```

Not bad. And surprisingly, a vec3 dot costs the same as a vec4 dot. Regardless, the problem is that if we want to do multiple dot products, the cost scales linearly.

> **A tip for Windows:** the default x64 calling convention passes any vector argument by pointer, which is where the `vmovaps` and the memory operand above come from. Marking the function `__vectorcall` (or compiling with `/Gv` in clang-cl and MSVC) passes vectors in registers instead, as the System V ABI on Linux already does. `/Gv` leaves member functions out, so a member function that takes vectors by value needs `__vectorcall` either way. With it, the dot product compiles to:
>
> ```
> dotVectorcall(float vector[4], float vector[4]):
>     vmulps     xmm0, xmm1, xmm0
>     vshufpd    xmm1, xmm0, xmm0, 1
>     vaddps     xmm0, xmm0, xmm1
>     vmovshdup  xmm1, xmm0
>     vaddss     xmm0, xmm0, xmm1
>     ret
> ```
>
> ```
> dotVectorcall(float vector[4], float vector[4]):
>     vmulps     xmm0, xmm1, xmm0
>     vshufpd    xmm1, xmm0, xmm0, 1
>     vaddps     xmm0, xmm0, xmm1
>     vmovshdup  xmm1, xmm0
>     vaddss     xmm0, xmm0, xmm1
>     ret
> ```

Let’s try transposing the vec4 one, so that each component of the vectors are stored together as one vector:

```
struct Vec4Lanes {
    vec4 x;
    vec4 y;
    vec4 z;
    vec4 w;
};

vec4 dot(const Vec4Lanes& a, const Vec4Lanes& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
```

```
struct Vec4Lanes {
    vec4 x;
    vec4 y;
    vec4 z;
    vec4 w;
};

vec4 dot(const Vec4Lanes& a, const Vec4Lanes& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
```

The assembly:

```
dot(Vec4Lanes const&, Vec4Lanes const&):
    vmovaps      xmm0, xmmword ptr [rdx]
    vmovaps      xmm1, xmmword ptr [rdx + 16]
    vmovaps      xmm2, xmmword ptr [rdx + 32]
    vmovaps      xmm3, xmmword ptr [rdx + 48]
    vmulps       xmm0, xmm0, xmmword ptr [rcx]
    vfmadd231ps  xmm0, xmm1, xmmword ptr [rcx + 16]
    vfmadd231ps  xmm0, xmm2, xmmword ptr [rcx + 32]
    vfmadd231ps  xmm0, xmm3, xmmword ptr [rcx + 48]
    ret
```

```
dot(Vec4Lanes const&, Vec4Lanes const&):
    vmovaps      xmm0, xmmword ptr [rdx]
    vmovaps      xmm1, xmmword ptr [rdx + 16]
    vmovaps      xmm2, xmmword ptr [rdx + 32]
    vmovaps      xmm3, xmmword ptr [rdx + 48]
    vmulps       xmm0, xmm0, xmmword ptr [rcx]
    vfmadd231ps  xmm0, xmm1, xmmword ptr [rcx + 16]
    vfmadd231ps  xmm0, xmm2, xmmword ptr [rcx + 32]
    vfmadd231ps  xmm0, xmm3, xmmword ptr [rcx + 48]
    ret
```

Hardly any extra code generated, except we now generate 4 dot products at once, at the cost of a few loads, since the lanes are passed by reference.

What about doing 8 at the same time?

```
struct Vec8Lanes {
    vec8 x;
    vec8 y;
    vec8 z;
    vec8 w;
};

vec8 dot(const Vec8Lanes& a, const Vec8Lanes& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
```

```
struct Vec8Lanes {
    vec8 x;
    vec8 y;
    vec8 z;
    vec8 w;
};

vec8 dot(const Vec8Lanes& a, const Vec8Lanes& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
}
```

The assembly:

```
dot(Vec8Lanes const&, Vec8Lanes const&):
    vmovaps      ymm0, ymmword ptr [rdx]
    vmovaps      ymm1, ymmword ptr [rdx + 32]
    vmovaps      ymm2, ymmword ptr [rdx + 64]
    vmovaps      ymm3, ymmword ptr [rdx + 96]
    vmulps       ymm0, ymm0, ymmword ptr [rcx]
    vfmadd231ps  ymm0, ymm1, ymmword ptr [rcx + 32]
    vfmadd231ps  ymm0, ymm2, ymmword ptr [rcx + 64]
    vfmadd231ps  ymm0, ymm3, ymmword ptr [rcx + 96]
    ret
```

```
dot(Vec8Lanes const&, Vec8Lanes const&):
    vmovaps      ymm0, ymmword ptr [rdx]
    vmovaps      ymm1, ymmword ptr [rdx + 32]
    vmovaps      ymm2, ymmword ptr [rdx + 64]
    vmovaps      ymm3, ymmword ptr [rdx + 96]
    vmulps       ymm0, ymm0, ymmword ptr [rcx]
    vfmadd231ps  ymm0, ymm1, ymmword ptr [rcx + 32]
    vfmadd231ps  ymm0, ymm2, ymmword ptr [rcx + 64]
    vfmadd231ps  ymm0, ymm3, ymmword ptr [rcx + 96]
    ret
```

Same result.

Why doesn’t the compiler do this for us? Because it would have to change the data layout. A compiler will happily vectorize a loop over an array of floats, but turning your array of `vec4`s into four arrays of floats changes what every other piece of code reading that memory sees, so no compiler will reorder and transpose your data for you. That part is up to us.

## A more complex example

Doing many dot products is cool and all, but it doesn’t have much of a practical use on its own. Let’s try applying the same trick to an average frustum culler.

The math for those who are unfamiliar with it: A (camera) frustum consists of six planes with their normals pointing outwards. A plane is stored as `(n, d)`: its unit normal `n`, and `d`, its offset along the normal, chosen so that `dot(n, p) + d` is the signed distance from a point `p` to the plane. A point is in front of the plane when that distance is positive, and if a box is entirely in front of any one plane, we can cull it.

![A plane, its normal n and offset d, with the signed distances of a point in front of it and one behind it](https://streamhpc.com/wp-content/uploads/2026/10/plane.png)

![A camera frustum with a box inside it, a box that straddles its left plane and stays visible, and a box entirely in front of its right plane, which is culled](https://streamhpc.com/wp-content/uploads/2026/10/frustum.png)

A box is stored as its center and its half extent: the offset from the center to a corner along each axis, so its corners are `center ± halfExtent`. A simple way to cull it is to check if all eight corners are in front of a plane.

Sample code, where each plane is a plain `vec4` with the normal in `xyz` and the offset along the normal in `w`:

```
struct Box {
    vec3 center;
    vec3 halfExtent;
};

vec3 abs(vec3 v) {
    return __builtin_elementwise_abs(v);
}

bool outsidePlane(vec4 plane, const Box& box) {
    for (int c = 0; c < 8; c++) {
        vec3 corner = box.center + box.halfExtent * vec3{
            c & 1 ? 1.0f : -1.0f,
            c & 2 ? 1.0f : -1.0f,
            c & 4 ? 1.0f : -1.0f
        };

        if (dot(plane.xyz, corner) + plane.w < 0.0f) {
            return false;
        }
    }

    return true;
}

void cullNaive(uint64_t* results, const vec4* planes, const Box* boxes, uint32_t count) {
    for (uint32_t i = 0; i < count; i++) {
        bool visible = true;

        for (uint32_t p = 0; p < 6; p++) {
            if (outsidePlane(planes[p], boxes[i])) {
                visible = false;
                break;
            }
        }

        const uint32_t shift = i % 64;
        results[i / 64] = (results[i / 64] & ~(uint64_t(1) << shift)) | (uint64_t(visible) << shift);
    }
}
```

```
struct Box {
    vec3 center;
    vec3 halfExtent;
};

vec3 abs(vec3 v) {
    return __builtin_elementwise_abs(v);
}

bool outsidePlane(vec4 plane, const Box& box) {
    for (int c = 0; c < 8; c++) {
        vec3 corner = box.center + box.halfExtent * vec3{
            c & 1 ? 1.0f : -1.0f,
            c & 2 ? 1.0f : -1.0f,
            c & 4 ? 1.0f : -1.0f
        };

        if (dot(plane.xyz, corner) + plane.w < 0.0f) {
            return false;
        }
    }

    return true;
}

void cullNaive(uint64_t* results, const vec4* planes, const Box* boxes, uint32_t count) {
    for (uint32_t i = 0; i < count; i++) {
        bool visible = true;

        for (uint32_t p = 0; p < 6; p++) {
            if (outsidePlane(planes[p], boxes[i])) {
                visible = false;
                break;
            }
        }

        const uint32_t shift = i % 64;
        results[i / 64] = (results[i / 64] & ~(uint64_t(1) << shift)) | (uint64_t(visible) << shift);
    }
}
```

The cost is 13.4 ns per box. We can do better.

### A simple optimization

You can achieve the same result by testing only the corner with the lowest signed distance: `center - sign(n) * e`, one step against the normal on every axis. If even that corner is in front of the plane, the whole box is:

```
float distance = dot(n, c) - dot(abs(n), e) + d; // outside if distance >= 0
```

```
float distance = dot(n, c) - dot(abs(n), e) + d; // outside if distance >= 0
```

![A box entirely in front of a plane, which is culled, and a box straddling it, which is kept, each with its center, half extent and lowest corner](https://streamhpc.com/wp-content/uploads/2026/10/box-against-plane.png)

The second term is the distance from the center to that corner, measured along the normal, so one test replaces eight:

```
void cullNearestCorner(uint64_t* results, const vec4* planes, const Box* boxes, uint32_t count) {
    for (uint32_t i = 0; i < count; i++) {
        bool visible = true;

        for (uint32_t p = 0; p < 6; p++) {
            const float distance = dot(planes[p].xyz, boxes[i].center)
                                 - dot(abs(planes[p].xyz), boxes[i].halfExtent) + planes[p].w;

            if (distance >= 0.0f) {
                visible = false;
                break;
            }
        }

        const uint32_t shift = i % 64;
        results[i / 64] = (results[i / 64] & ~(uint64_t(1) << shift)) | (uint64_t(visible) << shift);
    }
}
```

```
void cullNearestCorner(uint64_t* results, const vec4* planes, const Box* boxes, uint32_t count) {
    for (uint32_t i = 0; i < count; i++) {
        bool visible = true;

        for (uint32_t p = 0; p < 6; p++) {
            const float distance = dot(planes[p].xyz, boxes[i].center)
                                 - dot(abs(planes[p].xyz), boxes[i].halfExtent) + planes[p].w;

            if (distance >= 0.0f) {
                visible = false;
                break;
            }
        }

        const uint32_t shift = i % 64;
        results[i / 64] = (results[i / 64] & ~(uint64_t(1) << shift)) | (uint64_t(visible) << shift);
    }
}
```

That’s 3.0 ns per box, so we’re already four times faster than the basic implementation.

#### The branch predictor

Going from 10,000 boxes to 100,000, the same loop suddenly takes 12.7 ns per box. That’s only 3 MB of data, read front to back, so memory isn’t the problem. To see what is, I timed a 1,000-box scene and cycled through a different number of scenes between runs:

Scenesns per box13.0163.0185.2207.33211.320013.3200 identical copies3.0

The last two rows touch the same amount of memory. The difference is that in the last one every scene is a copy, so the early outs come in the same order every time. The CPU predicts each branch before it knows the answer, and Zen 3 can memorize the early outs of about 16,000 boxes. So if your benchmark culls the same small scene in a loop, you’re mostly benchmarking the branch predictor. Here, it made the nearest-corner test look 4.4× faster than it is on new data.

### Culling multiple boxes at the same time

Now that our benchmark measures the culler rather than the branch predictor, back to the point of this post: making full use of the available SIMD width. We can just use templates to make the same code work on any type T, so float, double, vecN all work.

```
template <typename T>
struct Vec3Lanes {
    T x, y, z;
};

template <typename T>
T dot(const Vec3Lanes<T>& a, const Vec3Lanes<T>& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

template <typename T>
Vec3Lanes<T> cross(const Vec3Lanes<T>& a, const Vec3Lanes<T>& b) {
    return { a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x };
}
```

```
template <typename T>
struct Vec3Lanes {
    T x, y, z;
};

template <typename T>
T dot(const Vec3Lanes<T>& a, const Vec3Lanes<T>& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

template <typename T>
Vec3Lanes<T> cross(const Vec3Lanes<T>& a, const Vec3Lanes<T>& b) {
    return { a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x };
}
```

And then the boxes can be expanded similarly:

```
template <typename T>
struct Box3Lanes {
    Vec3Lanes<T> center, halfExtent;

    T getMinSignedDistance(vec4 plane) const {
        const vec3 n = plane.xyz, a = abs(n);
        return n.x * center.x - a.x * halfExtent.x
             + n.y * center.y - a.y * halfExtent.y
             + n.z * center.z - a.z * halfExtent.z
             + plane.w;
    }
};
```

```
template <typename T>
struct Box3Lanes {
    Vec3Lanes<T> center, halfExtent;

    T getMinSignedDistance(vec4 plane) const {
        const vec3 n = plane.xyz, a = abs(n);
        return n.x * center.x - a.x * halfExtent.x
             + n.y * center.y - a.y * halfExtent.y
             + n.z * center.z - a.z * halfExtent.z
             + plane.w;
    }
};
```

The boxes are stored in blocks of `Box3Lanes`, one box per lane, with the last block padded out. The number of lanes `W` is 8 with AVX2 and 4 with SSE, so the same code fills whatever register size we compile for:

```
#ifdef __AVX2__
constexpr uint32_t W = 8;
#else
constexpr uint32_t W = 4;
#endif

using floatW = float __attribute__((ext_vector_type(W)));
using intW = int32_t __attribute__((ext_vector_type(W)));
```

```
#ifdef __AVX2__
constexpr uint32_t W = 8;
#else
constexpr uint32_t W = 4;
#endif

using floatW = float __attribute__((ext_vector_type(W)));
using intW = int32_t __attribute__((ext_vector_type(W)));
```

A whole block can’t take the same early out, so the branch has to turn into a mask:

```
template <typename P>
intW visibleMask(const Box3Lanes<floatW>& block, const P* planes) {
    intW visible = intW(-1);
    for (uint32_t p = 0; p < 6; p++) {
        visible &= block.getMinSignedDistance(planes[p]) < 0.0f;
    }
    return visible;
}

[[gnu::always_inline]] inline void writeLanes(uint64_t* results, intW visible, uint32_t first, uint32_t count) {
    for (uint32_t lane = 0; lane < W && first + lane < count; lane++) {
        const uint32_t i = first + lane;
        const uint64_t held = visible[lane] & 1;
        results[i / 64] = (results[i / 64] & ~(uint64_t(1) << (i % 64))) | (held << (i % 64));
    }
}

void cullLanes(uint64_t* results, const vec4* planes, const Box3Lanes<floatW>* blocks, uint32_t count) {
    for (uint32_t first = 0; first < count; first += W) {
        writeLanes(results, visibleMask(blocks[first / W], planes), first, count);
    }
}
```

```
template <typename P>
intW visibleMask(const Box3Lanes<floatW>& block, const P* planes) {
    intW visible = intW(-1);
    for (uint32_t p = 0; p < 6; p++) {
        visible &= block.getMinSignedDistance(planes[p]) < 0.0f;
    }
    return visible;
}

[[gnu::always_inline]] inline void writeLanes(uint64_t* results, intW visible, uint32_t first, uint32_t count) {
    for (uint32_t lane = 0; lane < W && first + lane < count; lane++) {
        const uint32_t i = first + lane;
        const uint64_t held = visible[lane] & 1;
        results[i / 64] = (results[i / 64] & ~(uint64_t(1) << (i % 64))) | (held << (i % 64));
    }
}

void cullLanes(uint64_t* results, const vec4* planes, const Box3Lanes<floatW>* blocks, uint32_t count) {
    for (uint32_t first = 0; first < count; first += W) {
        writeLanes(results, visibleMask(blocks[first / W], planes), first, count);
    }
}
```

This runs at 1.24 ns per box with AVX2 and 2.87 ns with SSE. On AVX2 that’s 10× faster than the nearest-corner test on fresh data. The SSE number is disappointing, though. Against the nearest-corner test with a trained predictor it’s only 1.3× faster, which isn’t much to show for four lanes. So let’s look at the assembly.

## The assembly in question

For one block of eight boxes against six planes, the math compiles to:

- 6 loads;
- 6 vmulps and 30 vfmadd231ps;
- 6 vcmpltps and 5 vandps to combine the masks.

Those 53 instructions are fine. The problem is that the whole loop is about 220.

**The frustum is rebuilt in every iteration.**

```
vandps        xmm7, xmm3, xmmword ptr [rdx]   ; abs(normal) of plane 0
vbroadcastss  ymm0, xmm7                      ; splat |n.x|
vmovups       ymm1, ymmword ptr [rsp + 48]    ; reload a permutation...
vpermps       ymm5, ymm1, ymm7                ; ...that splats |n.y|
```

```
vandps        xmm7, xmm3, xmmword ptr [rdx]   ; abs(normal) of plane 0
vbroadcastss  ymm0, xmm7                      ; splat |n.x|
vmovups       ymm1, ymmword ptr [rsp + 48]    ; reload a permutation...
vpermps       ymm5, ymm1, ymm7                ; ...that splats |n.y|
```

Every block gets 30 `vbroadcastss`, 12 `vpermps` and 6 `vandps`, and none of them have anything to do with the block. The compiler does this because six planes need 42 splats and AVX2 only has 16 `ymm` registers. Its register allocator figures that recomputing a broadcast is cheaper than spilling it and loading it back. For a plain broadcast from memory that’s true, but it redoes the `abs` and the permutes too.

**The results are written one bit at a time.**

```
vpextrd  r9d, xmm3, 3                  ; take one lane out of the mask
mov      r15d, r10d
and      r15b, 56                      ; the block's first bit within the word
mov      ebp, 8
shlx     rbp, rbp, r15
andn     rbp, rbp, r11                 ; clear the lane's bit
or       r15b, 3                       ; the lane's bit within the word
shlx     r11, r9, r15                  ; shift the lane to that bit
or       r11, rbp
mov      qword ptr [rcx + 8*rsi], r11  ; store the word
lea      r9, [rax - 4]
cmp      r9d, r10d                     ; was that the last object?
je       .LBB12_11
```

```
vpextrd  r9d, xmm3, 3                  ; take one lane out of the mask
mov      r15d, r10d
and      r15b, 56                      ; the block's first bit within the word
mov      ebp, 8
shlx     rbp, rbp, r15
andn     rbp, rbp, r11                 ; clear the lane's bit
or       r15b, 3                       ; the lane's bit within the word
shlx     r11, r9, r15                  ; shift the lane to that bit
or       r11, rbp
mov      qword ptr [rcx + 8*rsi], r11  ; store the word
lea      r9, [rax - 4]
cmp      r9d, r10d                     ; was that the last object?
je       .LBB12_11
```

That’s thirteen instructions per lane, about 100 per block, which is more than the math itself.

## Splatting the planes once

So we do the splatting ourselves, once, before the loop, and keep the results in memory:

```
template <typename T>
struct PlaneLanes {
    Vec3Lanes<T> normal, absNormal;
    T constant;
};

// Broadcasts each component of v into its own register
Vec3Lanes<floatW> splat(vec3 v) {
    return { floatW(v.x), floatW(v.y), floatW(v.z) };
}

PlaneLanes<floatW> splatPlane(vec4 plane) {
    return { splat(plane.xyz), splat(abs(plane.xyz)), floatW(plane.w) };
}

void cullLanesSplatOnce(uint64_t* results, const vec4* frustum, const Box3Lanes<floatW>* blocks, uint32_t count) {
    PlaneLanes<floatW> planes[6];
    for (uint32_t p = 0; p < 6; p++)
        planes[p] = splatPlane(frustum[p]);

    for (uint32_t first = 0; first < count; first += W) {
        writeLanes(results, visibleMask(blocks[first / W], planes), first, count);
    }
}
```

```
template <typename T>
struct PlaneLanes {
    Vec3Lanes<T> normal, absNormal;
    T constant;
};

// Broadcasts each component of v into its own register
Vec3Lanes<floatW> splat(vec3 v) {
    return { floatW(v.x), floatW(v.y), floatW(v.z) };
}

PlaneLanes<floatW> splatPlane(vec4 plane) {
    return { splat(plane.xyz), splat(abs(plane.xyz)), floatW(plane.w) };
}

void cullLanesSplatOnce(uint64_t* results, const vec4* frustum, const Box3Lanes<floatW>* blocks, uint32_t count) {
    PlaneLanes<floatW> planes[6];
    for (uint32_t p = 0; p < 6; p++)
        planes[p] = splatPlane(frustum[p]);

    for (uint32_t first = 0; first < count; first += W) {
        writeLanes(results, visibleMask(blocks[first / W], planes), first, count);
    }
}
```

`Box3Lanes` gets a second overload for the splatted planes:

```
T getMinSignedDistance(const PlaneLanes<T>& p) const {
    return dot(p.normal, center) - dot(p.absNormal, halfExtent) + p.constant;
}
```

```
T getMinSignedDistance(const PlaneLanes<T>& p) const {
    return dot(p.normal, center) - dot(p.absNormal, halfExtent) + p.constant;
}
```

Now the compiler reads the planes straight from the stack as memory operands of the FMAs:

```
vfmadd231ps  ymm3, ymm15, ymmword ptr [rsp + 1056]
```

```
vfmadd231ps  ymm3, ymm15, ymmword ptr [rsp + 1056]
```

That gets AVX2 down to 0.98 ns per box and SSE to 1.85 ns. SSE benefits more because its blocks only hold four boxes, so it was rebuilding the frustum twice as often.

## Writing the block at once

The eight result bits of a block make up exactly one byte, so we can turn the mask into one bit per lane and store all eight at once. With SSE, two blocks of four share a byte, so each one writes its half:

```
using boolW = bool __attribute__((ext_vector_type(W)));

void writeBlock(uint64_t* results, intW visible, uint32_t first) {
    const boolW bits = __builtin_convertvector(visible, boolW);    // one bit per lane
    uint8_t& byte = reinterpret_cast<uint8_t*>(results)[first / 8];

    if constexpr (W == 8) {
        byte = __builtin_bit_cast(uint8_t, bits);    // store all eight
    } else {
        const uint32_t shift = first % 8;            // two blocks of four share a byte
        const uint8_t held = __builtin_bit_cast(uint8_t, bits) & 0xF;
        byte = (byte & ~(0xF << shift)) | (held << shift);
    }
}

void cullLanesBlockWrite(uint64_t* results, const vec4* planes, const Box3Lanes<floatW>* blocks, uint32_t count) {
    uint32_t first = 0;
    for (; first + W <= count; first += W) {
        writeBlock(results, visibleMask(blocks[first / W], planes), first);
    }

    if (first < count) {    // only the last block, if it isn't full, still goes lane by lane
        writeLanes(results, visibleMask(blocks[first / W], planes), first, count);
    }
}
```

```
using boolW = bool __attribute__((ext_vector_type(W)));

void writeBlock(uint64_t* results, intW visible, uint32_t first) {
    const boolW bits = __builtin_convertvector(visible, boolW);    // one bit per lane
    uint8_t& byte = reinterpret_cast<uint8_t*>(results)[first / 8];

    if constexpr (W == 8) {
        byte = __builtin_bit_cast(uint8_t, bits);    // store all eight
    } else {
        const uint32_t shift = first % 8;            // two blocks of four share a byte
        const uint8_t held = __builtin_bit_cast(uint8_t, bits) & 0xF;
        byte = (byte & ~(0xF << shift)) | (held << shift);
    }
}

void cullLanesBlockWrite(uint64_t* results, const vec4* planes, const Box3Lanes<floatW>* blocks, uint32_t count) {
    uint32_t first = 0;
    for (; first + W <= count; first += W) {
        writeBlock(results, visibleMask(blocks[first / W], planes), first);
    }

    if (first < count) {    // only the last block, if it isn't full, still goes lane by lane
        writeLanes(results, visibleMask(blocks[first / W], planes), first, count);
    }
}
```

The partial last block is handled after the loop rather than with a branch inside it. That matters more than it looks: when the mask is created in one basic block and turned into bits in another, Clang no longer knows every lane is either all ones or all zeros, and replaces the single `vmovmskps` with a chain of shuffles and packs.

The writeback now looks like this:

```
vmovmskps  r10d, ymm2                    ; one bit per lane
mov        byte ptr [rcx + rax], r10b    ; store all eight
```

```
vmovmskps  r10d, ymm2                    ; one bit per lane
mov        byte ptr [rcx + rax], r10b    ; store all eight
```

With both changes in place, AVX2 takes 0.67 ns per box<sup>[1](https://streamhpc.com/blog/2026-10-28/making-simd-code-scale-to-any-vector-width/#footnote-1)</sup> and SSE 1.84 ns. The loop is down to about 95 straight-line instructions per block of eight, or about 3 cycles per box.

## Results

All times are in nanoseconds per box, for 10,000 boxes. The numbers in brackets are for 100,000 boxes, which is too many for the branch predictor to memorize.

MethodAVX2, 8 lanesSSE4.2, 4 lanesThe naive method13.4 (17.2)15.8 (19.1)Nearest corner3.04 (12.7)3.77 (13.9)One box per lane1.242.87Splatting the planes once0.981.85Block writeback, without splatting1.042.69Splatting once and block writeback0.67<sup>[1](https://streamhpc.com/blog/2026-10-28/making-simd-code-scale-to-any-vector-width/#footnote-1)</sup>1.84

Splatting once helps both, SSE the most (1.55× on its own, against 1.27× on AVX2), while the block writeback alone does less (1.19× on AVX2, 1.07× on SSE). On AVX2 the two compound, since once the splats are gone, the bit-by-bit writeback is most of what’s left; together they make the one-box-per-lane version 1.85× faster. On SSE the writeback adds nothing once the planes are splatted, and the combination stays at 1.56×. From start to finish, the culler got about 20× faster, or 25× on data the branch predictor hadn’t seen before.

## Conclusion

Most of the speedup comes from turning vectors into lanes. Eight dot products cost three instructions, and the early outs become masks. The less obvious part is that the straightforward SIMD version spent more instructions moving data around than on the actual math, and it took two more changes to get rid of that. Precompute whatever the compiler can’t keep in registers, and write the results a whole block at a time. You’ll run into the same two problems in any loop that tests lots of objects against a few shared values.

<sup>1</sup> Only when the stack happens to be 32-byte aligned. Windows and Linux only guarantee 16 bytes, and Clang spills the splatted planes’ `ymm` registers with unaligned stores rather than realigning the stack, so in some processes half of the reloads straddle a cache line, and the same loop takes 0.99 ns. Adding `__attribute__((force_align_arg_pointer))` to the function makes Clang realign the stack in its prologue, which gives 0.67 ns every time.