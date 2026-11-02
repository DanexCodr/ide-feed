You want to see something… spooky? Do you want to hear a story, so haunting, so bone-chilling, it keeps you up at night? Well, let’s look at this program that grants permissions:

```
#include <iostream>
#include <string>
#include <string_view>

std::string_view Sanitize(const std::string& input) {
  std::string_view sanitized = input;
  while (!sanitized.empty() && sanitized.front() == ' ') { 
    sanitized.remove_prefix(1);
  }
  return sanitized;
}

int main() {
  std::cout << std::boolalpha; 
  std::string_view username = Sanitize("foobarbazboo");
  std::string admin_id = "root_1231231";
  std::cout << "Grant foobarbazboo root permissions = " << (username == admin_id) << "\n";
  return 0;
}
```

When I compile and run this code (`clang++-19 -std=c++17 -O0 -Wall -Wextra -Wpedantic cursed.cpp -o cursed_clang && ./cursed_clang`), everything works fine and my user `foobarbazboo` does not get root permissions:

```
Grant foobarbazboo root permissions = false
```

However, if I compile this code in a forest, at midnight on halloween, on top of a Ouija board, after saying “Candyman” in front of a mirror 5 times, and changing the optimization flag to `-O2`, this program will mysteriously grant `foobarbazboo` root permissions…

```
clang++-19 -std=c++17 -O2 -Wall -Wextra -Wpedantic cursed.cpp -o cursed_clang_optimized && ./cursed_clang_optimized

Grant foobarbazboo root permissions = true
```

Is this the work of g-g-ghosts? Is my computer h-h-haunted?

- No - you can reproduce this on your computer as well.

Is C++17 c-c-cursed?

- Yes, but not by the supernatural. This can happen on C++20 and C++23 as well:

```
clang++-19 -std=c++20 -O2 -Wall -Wextra -Wpedantic cursed.cpp -o cursed_clang_c20 && ./cursed_clang_c23

Grant foobarbazboo root permissions = true

clang++-19 -std=c++23 -O2 -Wall -Wextra -Wpedantic cursed.cpp -o cursed_clang_c23 && ./cursed_clang_c17
```

Is my compiler c-c-cursed?

- No, because GCC will do the same thing:

```
g++ -std=c++17 -O0 -Wall -Wextra -Wpedantic cursed.cpp -o cursed_gcc && ./cursed_gcc
Grant foobarbazboo root permissions = false

g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic cursed.cpp -o cursed_gcc_optimized && ./cursed_gcc_optimized
Grant foobarbazboo root permissions = true
```

# What’s going on

As you can guess, this is an example of undefined behavior causing unintuitive results.

Even though this is a funny example, I doubt a bug like this will surface in the wild (nor be easily exploited) as this behavior is incredibly hard to reproduce.

For example, this only works because the string `foobarbazboo` is the same length as `admin_id`, and is passed as an inline parameter. If you change the input length or refactor the program to store `foobarbazboo` in a temporary variable, the behavior goes away.

Even if you didn’t know anything about UB, I think most people would think this code is ill-formed and weird. A handful of readability/refactoring principles will eliminate this particular behavior. For instance, refactoring `admin_id` to be a singleton/global variable will make the program behave correctly.