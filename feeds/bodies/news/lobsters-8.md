I often find myself writing (by which I mean generating) functions to convert enums to strings. A naïve implementation of such a function might look like:

```
const char* dxgi_format_to_string(unsigned x) {
  switch (x) {
  case  0: return "UNKNOWN";
  case  1: return "R32G32B32A32_TYPELESS";
  case  2: return "R32G32B32A32_FLOAT";
  case  3: return "R32G32B32A32_UINT";
  case  4: return "R32G32B32A32_SINT";
  case  5: return "R32G32B32_TYPELESS";
  case  6: return "R32G32B32_FLOAT";
  case  7: return "R32G32B32_UINT";
  case  8: return "R32G32B32_SINT";
  case  9: return "R16G16B16A16_TYPELESS";
  case 10: return "R16G16B16A16_FLOAT";
  case 11: return "R16G16B16A16_UNORM";
  case 12: return "R16G16B16A16_UINT";
  case 13: return "R16G16B16A16_SNORM";
  case 14: return "R16G16B16A16_SINT";
  case 15: return "R32G32_TYPELESS";
  case 16: return "R32G32_FLOAT";
  case 17: return "R32G32_UINT";
  case 18: return "R32G32_SINT";
  case 19: return "R32G8X24_TYPELESS";
  case 20: return "D32_FLOAT_S8X24_UINT";
  case 21: return "R32_FLOAT_X8X24_TYPELESS";
  case 22: return "X32_TYPELESS_G8X24_UINT";
  default: return NULL;
  }
}
```

Compiling the above with a modern gcc at `-O0` or `-O1` gives some fairly horrible assembly code. Thankfully, at `-O2` and above, a modern gcc can rewrite it to something more along the lines of:

```
const char* dxgi_format_to_string(unsigned x) {
  static const char* const cases[] = {
    "UNKNOWN",
    "R32G32B32A32_TYPELESS",
    "R32G32B32A32_FLOAT",
    "R32G32B32A32_UINT",
    "R32G32B32A32_SINT",
    "R32G32B32_TYPELESS",
    "R32G32B32_FLOAT",
    "R32G32B32_UINT",
    "R32G32B32_SINT",
    "R16G16B16A16_TYPELESS",
    "R16G16B16A16_FLOAT",
    "R16G16B16A16_UNORM",
    "R16G16B16A16_UINT",
    "R16G16B16A16_SNORM",
    "R16G16B16A16_SINT",
    "R32G32_TYPELESS",
    "R32G32_FLOAT",
    "R32G32_UINT",
    "R32G32_SINT",
    "R32G8X24_TYPELESS",
    "D32_FLOAT_S8X24_UINT",
    "R32_FLOAT_X8X24_TYPELESS",
    "X32_TYPELESS_G8X24_UINT",
  };
  if (x > 22u) return NULL;
  return cases[x];
}
```

The assembly code for this is much nicer, although the table of pointers still takes up more space than I'd like (and that's before you account for each table entry needing a relocation entry...). It can be made smaller by concatenating all the strings together into a single contiguous piece of memory and then using a table of offsets into that memory, taking advantage of the fact that a relative offset can be much smaller than a pointer:

```
const char* dxgi_format_to_string(unsigned x) {
  const char* cases =
    /*  0*/ "UNKNOWN\0"
    /*  8*/ "R32G32B32A32_TYPELESS\0"
    /* 30*/ "R32G32B32A32_FLOAT\0"
    /* 49*/ "R32G32B32A32_UINT\0"
    /* 67*/ "R32G32B32A32_SINT\0"
    /* 85*/ "R32G32B32_TYPELESS\0"
    /*104*/ "R32G32B32_FLOAT\0"
    /*120*/ "R32G32B32_UINT\0"
    /*135*/ "R32G32B32_SINT\0"
    /*150*/ "R16G16B16A16_TYPELESS\0"
    /*172*/ "R16G16B16A16_FLOAT\0"
    /*191*/ "R16G16B16A16_UNORM\0"
    /*210*/ "R16G16B16A16_UINT\0"
    /*228*/ "R16G16B16A16_SNORM\0"
    /*247*/ "R16G16B16A16_SINT\0"
    /*265*/ "R32G32_TYPELESS\0"
    /*281*/ "R32G32_FLOAT\0"
    /*294*/ "R32G32_UINT\0"
    /*306*/ "R32G32_SINT\0"
    /*318*/ "R32G8X24_TYPELESS\0"
    /*336*/ "D32_FLOAT_S8X24_UINT\0"
    /*357*/ "R32_FLOAT_X8X24_TYPELESS\0"
    /*382*/ "X32_TYPELESS_G8X24_UINT";
  static const uint16_t offsets[] = {
      0,
      8,
     30,
     49,
     67,
     85,
    104,
    120,
    135,
    150,
    172,
    191,
    210,
    228,
    247,
    265,
    281,
    294,
    306,
    318,
    336,
    357,
    382,
  };
  if (x > 22u) return NULL;
  return cases + offsets[x];
}
```

This is pretty good, but the `offsets` table can be made even smaller. Consider the function `x ↦ offsets[x]`: it maps `0` to `0` and `22` to `382`, so one possible linear approximation of this could be `x ↦ x * int(round(382.0 / 22.0))`, also known as `x ↦ x * 17`. It is rarely the case that `x * 17` *exactly equals* `offsets[x]`, but the difference between `x * 17` and `offsets[x]` happens to always end up being in the range `[-9, +10]`. As such, the `offsets` table can be replaced with `x * 17` and a table of corrections, where the corrections table occupies less space than the original offsets table:

```
const char* dxgi_format_to_string(unsigned x) {
  const char* cases =
    /*  0*/ "UNKNOWN\0"
    /*  8*/ "R32G32B32A32_TYPELESS\0"
    /* 30*/ "R32G32B32A32_FLOAT\0"
    /* 49*/ "R32G32B32A32_UINT\0"
    /* 67*/ "R32G32B32A32_SINT\0"
    /* 85*/ "R32G32B32_TYPELESS\0"
    /*104*/ "R32G32B32_FLOAT\0"
    /*120*/ "R32G32B32_UINT\0"
    /*135*/ "R32G32B32_SINT\0"
    /*150*/ "R16G16B16A16_TYPELESS\0"
    /*172*/ "R16G16B16A16_FLOAT\0"
    /*191*/ "R16G16B16A16_UNORM\0"
    /*210*/ "R16G16B16A16_UINT\0"
    /*228*/ "R16G16B16A16_SNORM\0"
    /*247*/ "R16G16B16A16_SINT\0"
    /*265*/ "R32G32_TYPELESS\0"
    /*281*/ "R32G32_FLOAT\0"
    /*294*/ "R32G32_UINT\0"
    /*306*/ "R32G32_SINT\0"
    /*318*/ "R32G8X24_TYPELESS\0"
    /*336*/ "D32_FLOAT_S8X24_UINT\0"
    /*357*/ "R32_FLOAT_X8X24_TYPELESS\0"
    /*382*/ "X32_TYPELESS_G8X24_UINT";
  static const int8_t corrections[] = {
     0,
    -9,
    -4,
    -2,
    -1,
     0,
     2,
     1,
    -1,
    -3,
     2,
     4,
     6,
     7,
     9,
    10,
     9,
     5,
     0,
    -5,
    -4,
     0,
     8,
  };
  if (x > 22u) return NULL;
  return cases + ((long)(x * 17u) + corrections[x]);
}
```

There's a general pattern here: an exact function can be computed via a fast but incorrect approximation followed by a table of corrections, and doing so can be profitable if this allows a smaller table than other approaches would require. This is not a novel idea, but it still needs repeating from time to time, even if only to remind compiler developers that there are still optimisations they're missing.