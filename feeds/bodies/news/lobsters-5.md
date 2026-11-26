The [named integer](https://ziglang.org/devlog/2024/#2024-11-04) or [Newtype Index pattern](https://matklad.github.io/2025/12/23/zig-newtype-index-pattern.html) prevents mixing up indexes on different arrays.

The above examples were not particularly illuminating to me. Andrew’s example don’t show much of how to enforce the safety at call site: any caller could call `backingInt` (it used to be `@intFromEnum`) to recover a numerical index and pass it to the wrong array, or access array elements with a plain integer. And matklad’s one focus on building a tree data structure in a neat way, but that’s a totally different challenge that the introductory problem of mixing array indexes, so it was not a super convincing illustration for me.

In practice, to make good use of the pattern, a getter helper is required as the conventional way of accessing elements of the array. It can be a method on the array type—or the index type.

```
// Declaration
const Elem = struct {...};
const Array = struct {
    items: []Elem,

    const Index = enum(u32) { _ };

    fn get(a: *Array, i: Index) *Elem {
        return &a.items[@backingInt(i)];
    }
};

// Usage
const a = Array{ .items = &.{...} };

var i: Index = @fromBackingInt(57);
_ = a.get(i);

_ = a.get(57); // Does not compile: wrong type.
_ = a[57]; // Possible, but discouraged by the existence of `Array.get`.
```

## A struct of array example

In a struct of array data structure, it is particularly valuable to have one typed index per slice rather than relying on careful naming.

Consider this spreadsheet example where it’s easy to mix up indexes:

```
pub const Sheet = struct {
    row_height: []f32,
    col_width: []f32,
};

var s: Sheet = .{...};
var r: usize = 0; // Row index.
var c: usize = 0; // Column index.

// User changes the column width.
s.col_width[r].* = new_col_width; // bug: access row data with a column indice!
```

We can prevent such bug by enforcing compile time checking of field access with typed indexes.

```
pub const Sheet = struct {
    row_height: []f32,
    col_width: []f32,

    pub const Row = enum(u32) { _ };
    pub const Column = enum(u32) { _ };

    pub fn getRowHeight(s: *Sheet, r: Row) *f32 {
        return &s[@backingInt(r)];
    }

    pub fn getColWidth(s: *Sheet, c: Column) *f32 {
        return &s[@backingInt(c)];
    }
};

var s: Sheet = .{ ... };
var r: Sheet.Row = @fromBackingInt(0); // Typed row index.
var c: Sheet.Column = @fromBackingInt(0); // Typed column index.

// User changes the column width.
const new_col_width: f32 = undefined;

s.getColWidth(r).* = new_col_width; // Comptime error: wrong type.
s.getColWidth(c).* = new_col_width; // Yes!

s.col_width[@backingInt(r)]  // Possible, but very intentional.

s.col_width[57]  // Possible, but discouraged by
                 // convention given by Sheet decls
                 // and documentation.
```

## Generic recipe

Its clumsy to keep one index type and one accessor per field. We can use a bit of comptime to streamline the pattern, and make the recipe more generic to fit arbitrary structs. Here is a complete example.

```
pub const Sheet = struct {
    row_height: []f32,
    row_hidden: []bool,

    col_width: []f32,
    col_hidden: []bool,

    title: []const u8,

    pub const Field = enum {
        row_height,
        row_hidden,
        col_width,
        col_hidden,
    };

    comptime {
        for (std.enums.values(Field)) |f| {
            std.debug.assert(@hasField(Sheet, @tagName(f)));
        }
    }

    pub const Kind = enum { row, col };

    pub fn kindOf(f: Field) Kind {
        return switch (f) {
            .row_height, .row_hidden => .row,
            .col_width, .col_hidden => .col,
        };
    }

    pub fn Index(comptime k: Kind) type {
        return enum(u32) {
            _,
        };
    }

    pub fn at(
        s: *Sheet,
        comptime f: Field,
        i: Index(kindOf(f)),
    ) *std.meta.Elem(@FieldType(Sheet, @tagName(f))) {
        return &@field(s, @tagName(f))[@backingInt(i)];
    }
};
```

Let’s walk it step by step.

```
pub const Sheet = struct {
    row_height: []f32,
    row_hidden: []bool,

    col_width: []f32,
    col_hidden: []bool,

    title: []const u8,
};
```

Our spreadsheet has now several fields: a title, and row and column properties. When iterating over them, we have two kinds of indexes: row indexes and column indexes. Adding typed indexes is attractive to prevent callers from mixing them up.

```
pub const Field = enum {
    row_height,
    row_hidden,
    col_width,
    col_hidden,
};
```

This enum gives us a way of referencing all the struct fields for which we will construct a typed indexed. If all fields were to be indexed, we would have used `std.meta.FieldEnum(Sheet)`, but our spreadsheet has a title.

```
comptime {
    for (std.enums.values(Field)) |f| {
        std.debug.assert(@hasField(Sheet, @tagName(f)));
    }
}
```

This checks at compile time that each `Field` enum variant name is indeed a field inside `Sheet`. As we’ll see later, we will have to access `Sheet`’s fields by *name*, so it’s good to check the names of `Field` variants match the names of `Sheet` fields.

```
pub const Kind = enum { row, col };
```

This defines the kind of type indexes we’ll construct: one for row data slices and one for columns data slices. Each indexed field of `Sheet` has one correct typed index kind. We match them with an exhaustive switch over `Field`.

```
pub fn kindOf(f: Field) Kind {
    return switch(f) {
        .row_height, .row_hidden => .row,
        .col_width, .col_hidden => .col,
    }
}
```

We now have all we need to construct the two typed indexes of kinds `.row` and `.col`. A generic function returning a type at comptime is how to do it.

```
pub fn Index(comptime k: Kind) type {
    return enum(u32) {
        _,
    };
}
```

The typed index type for row is `Sheet.Index(.row)`, and for colum it is `Sheet.Index(.col)`. Note the title case of the `Index` function, matching Zig’s convention for types.

Remains to give a way of making use of these types.

```
pub fn at(
    s: *Sheet,
    comptime f: Field,
    i: Index(kindOf(f)),
) *std.meta.Elem(@FieldType(Sheet, @tagName(f))) {
    return &@field(s, @tagName(f))[@backingInt(i)];
}
```

This part may look complex if you are not familiar with comptime-enabled generics in Zig, so let’s be precise. This defines a method on `Sheet` that requires `f` to be a `Field` instance known at compile time. This allow to infer at compile time both the type of `i` and the return type.

`Index(kindOf(f))` is just a chain of function calls on a known value. So it is comptime known. And most importantly, *the type of `i` is bound to the one of `f` at compile time.* Given the body of `Sheet.kindOf`, it’s easy to see that `s.at(.row_width, i)` will compile only if `i` has type `Index(.row)`!

The return type of Zig function must be comptime known, and it is the case here by using some reflection. `@FieldType(Sheet, name)` returns the type of the field of `Sheet` named `name` (given as a `[]const u8`). `@tagName(f)` gives just that for the input enum variant. `std.meta.Elem` returns the element type for a collection type (here a slice). Finally, we return a pointer to allow the caller to mutate, but a value would work just fine for a read-only case.

This gives us a clear usage at call site.

```
var s: Sheet = .{ ... };
var r: Sheet.Index(.row) = @fromBackingInt(0); // Typed row index.
var c: Sheet.Index(.col) = @fromBackingInt(0); // Typed column index.

// Several iterations later,
// the column width must be changed.

const new_col_width: f32 = 57;
s.at(.col_width, r).* = new_col_width; // comptime error: wrong type.
s.at(.col_width, c).* = new_col_width; // ok: Sheet.Index(Sheet.kindOf(.col_width)) == Sheet.Index(.col).
```

So neat!

The `Sheet.Index(.row)` syntax is particularly lovely: a method call feeling like a qualified concrete type.

Still, as I hinted earlier, this design it not completely hermetic to bugs. Nothing prevents you from forging a `Sheet.Index(.row)` from any integer with `@fromBackingInt`. And opaque types are really just for interaction with C.

Also, any caller can access `Sheet` fields directly (Zig has no notion of private fields.).

```
s.at(.col_width, @fromBackingInt(@backingInt(r)))  // Possible, but very intentional.
s.col_width[@backingInt(r)]  // Possible, but very intentional.
s.col_width[57]  // Possible, but discouraged by convention given by Sheet decls and documentation.
```

As for all Zig code, one must follow documented usage (“Direct access is discouraged. Use `Sheet.at`.”) and make good use of the public methods by proactively inspecting types.