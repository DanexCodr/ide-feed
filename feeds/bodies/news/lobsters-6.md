Welcome! This tutorial shows you how to write a small drawing app in Rust, in the spirit of Paint. We open a window, draw rectangles, circles and lines with the mouse, move them around, pick a color, and export the drawing as an image.

We start from an empty `cargo new`. By the end, you have about 800 lines of Rust spread over fifteen or so files, with a single dependency: [minifb](https://crates.io/crates/minifb), which opens the window and gives us the keyboard and the mouse. Everything else we write ourselves: filling pixels, drawing a line, checking whether the mouse is on a circle, converting an HSV color to RGB.

The tutorial is split into 12 chapters. Each one ends with a program that compiles and does something you can see, even if at first it's just an image file with a red square in it.

## Why this tutorial[#](https://www.buildyourownpaint.com/en#why-this-tutorial)

I'm a developer and I've been doing data science for several years. But in my free time, I've always been drawn to low-level things: bare metal, and how a computer works at the very bottom of the stack.

I wrote this tutorial with someone in mind who is starting out, or simply curious, and who wonders how a program ends up showing something on the screen. It covers the basics of rasterization, that is, how a rectangle or a circle turns into pixels, starting from nothing and in small pieces you can understand one at a time.

That's mostly what I'd like to show: by moving forward step by step, in a language close to the machine, you end up with something that works and that you wrote entirely yourself. It takes time, but there's nothing magic about it. If this tutorial takes away a bit of that mystery and makes a few beginners want to look further down, it will have done its job.

## Who it's for[#](https://www.buildyourownpaint.com/en#who-its-for)

This tutorial is a way to learn Rust by building something. I assume you've read the first chapters of the [Rust Book](https://doc.rust-lang.org/book/) (variables, functions, `if`, loops) but haven't written a real program with it yet. The heavier concepts, like enums, traits, borrowing, modules or error handling, come along chapter by chapter, when we need them.

You don't need to know anything about graphics. As for math, you need Pythagoras for circles and a projection to tell whether the mouse is on a line. I explain it when we get there.

Each chapter has boxes that explain why Rust does things the way it does. If you already know, skip them. Same for the exercises at the end of each chapter: they're there if you want practice, but nothing that follows depends on them.

I'd still recommend typing the code rather than copy-pasting it. It's slower, but typing is how you make mistakes, and fixing them is how you end up understanding what the compiler is trying to tell you.

## What it isn't[#](https://www.buildyourownpaint.com/en#what-it-isnt)

Let's be upfront: at the end, you won't have GIMP. There's no brush, no layers, no undo. And technically, our app isn't even really a Paint. Paint paints pixels that can't be moved once they're down, whereas we keep a list of shapes that can be selected and moved. We come back to this in chapter 11, and the [Going further](https://www.buildyourownpaint.com/en/further) page has ideas for adding a brush, a paint bucket or undo.

## Contents[#](https://www.buildyourownpaint.com/en#contents)

1. 00SetupWe install Rust, create the project and check that everything compiles.Duration 15 min
2. 012D vectorsWe write a Vec2 type with its operations, and try it out in the terminal.Duration 45 min
3. 02An image in memoryWe build an image pixel by pixel and save it in the PPM format.Duration 40 min
4. 03Drawing shapesWe pack each color into a single number, and draw rectangles, circles and lines pixel by pixel.Duration 50 min
5. 04A windowWe add our first dependency to open a window and keep showing the canvas in it.Duration 35 min
6. 05The mouseWe draw rectangles by clicking and dragging, with a preview that follows the mouse.Duration 1 h
7. 06Several shapesWe add circles and lines, and choose the tool with the keyboard.Duration 45 min
8. 07Selecting and movingWe click on a shape to select it, drag it to move it, and delete it with the keyboard.Duration 1 h 15
9. 08The toolbarWe add buttons in the top-right corner of the window to choose the tool with the mouse.Duration 40 min
10. 09ColorsWe add a color button that opens a picker, to choose the color of new shapes.Duration 1 h
11. 10SavingWe save the drawing to an image file, without the toolbar or the selection, and without overwriting previous files.Duration 30 min
12. 11Wrap-upNo code in this chapter. We step back to look at what we built and what we learned.Duration 15 min

After that, [Going further](https://www.buildyourownpaint.com/en/further) suggests ideas to keep going on your own, from freehand drawing to a version that runs in the browser.

## Following along with git[#](https://www.buildyourownpaint.com/en#following-along-with-git)

All the code is in the pages, you don't need anything else. But if you prefer, the [GitHub repo](https://github.com/theZackD/build-your-own-paint) has one tag per chapter: `git checkout ch05-mouse` gives you the exact code at the end of chapter 5, and `git diff ch04-window ch05-mouse` shows everything it adds. It's also handy to start again from a clean state if you get lost. The [Following along with git](https://www.buildyourownpaint.com/en/git) page explains all of this.

If you find a mistake, an unclear explanation or a piece of code that doesn't compile, open an issue on GitHub. It really helps.