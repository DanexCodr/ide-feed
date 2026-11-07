Meridian is a web-browser for MacOS built on [GPUI](https://www.gpui.rs) and [Servo](https://servo.org). Meridian is
    already quite useful to browse websites that are light on javascript and
    layouting features. The browser is highly configurable: fonts, keybinds,
    colors, tabs and all.

![Meridian with vertical tabs, showing the Meridian homepage](https://cdn.oppi.li/meridian/Screenshot%202026-11-05%20at%2018.47.10.png)

To try Meridian, you can use nix:

```
nix run git+https://tangled.org/oppi.li/meridian
```

The project is developed on [Tangled](https://tangled.org/oppi.li/meridian), all
    contributions are welcome, please do browse the list of [open issues](https://tangled.org/oppi.li/meridian/issues) if you
    are looking to contribute!

Meridian supports the following features:

![Right-click context menu over a link](https://cdn.oppi.li/meridian/Screenshot%202026-11-05%20at%2018.57.12.png)

*Context menu*

![Meridian in dark mode](https://cdn.oppi.li/meridian/Screenshot%202026-11-05%20at%2018.55.19.png)

*Dark mode*

![An article in reader view](https://cdn.oppi.li/meridian/Screenshot%202026-11-05%20at%2018.52.51.png)

*Reader view*

Under the hood, Meridian is written in Rust and built on GPUI and Servo.
    Web pages and browser state is managed by Servo. The browser's chrome is
    drawn by [gpui](https://www.gpui.rs), the UI framework behind
    the Zed editor. The glue code to interface servo with gpui lives in
    separate library, [gpui-servo](https://tangled.org/oppi.li/gpui-servo), which exposes
  Servo as an ordinary gpui component, so anybody can now write a servo-based
  browser in GPUI!