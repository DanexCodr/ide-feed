So I think [Janet](https://janet-lang.org/) is a pretty sweet little programming language. I've always found Lisp and Scheme interesting, but I could never get into them. Janet is small enough to try out and has enough convenient things to keep me from bouncing off it so far.

It comes with a pretty good standard library and data structures. It also has the "spork" library as basically the standard extension library. That one has a module called `httpf` which claims to be a minimal web framework. It has no docs or tutorial that I could find, so let's make a little server with it and see what it's all about.

```
(import "spork/httpf")

(def my-server (httpf/server)) # Create a server object

(defn my-index-route
  {:path "/"
   :render-mime "text/html"
   :doc "root of the server"} # this is "tagging" the function
  [request post-data] # our function arguments
  (def body [:html [:body [:h1 "Welcome to httpf"]
                    [:p "I am glad you are here!"]]])
  (setdyn :response-code 201) # setdyn is used to specify the HTTP Response code
  body)

# find all functions tagged with a :path and add them to router
(httpf/add-bindings-as-routes my-server) 

(httpf/listen my-server "localhost" "8000") # start the server on the host & port
```

Let's hit the server:

```
$ curl -i http://localhost:8000/
HTTP/1.1 201 Created
content-type: text/html
server: spork/httpf
Content-Length: 81

<html><body><h1>Welcome to httpf</h1><p>I am glad you are here!</p></body></html>
```

Okay seems nice. I've got comments in the code so you can follow along what's going on. We make a server object, define some functions that are tagged with `:path` that the server later finds. Then we can start the server on our host and port.

Janet doesn't have function annotations like Python or Java does. Instead we can put metadata on a function. In the Janet docs, I only ever saw it referenced to mark a function as deprecated. But you can put any key/value pair you want on a function. The HTTPF system then searches the functions in scope for those that have the `:path` metadata when we call the `add-bindgins-as-routes` function. It's a nice demo of that feature, and I wish official Janet docs made that more clear.

Overall, it has the basics, but you'll notice some odd choices. We use tags to define our returning Content-Type, it's not something we can decide in the function. Also, choosing "text/html" means we need to return a hiccup-style data structure that will get processed by [spork/htmlgen](https://janet-lang.org/spork/api/htmlgen.html), we don't get to build the HTML ourselves or use a different template system. Also, setting the HTTP Response Code is done via the `setdyn` call which makes it feel like setting a global variable. So one of my first impressions is that the way we build a HTTP response feels inelegant in this framework.

Our route functions take two parameters, `request` and `post-data`. The first is a general HTTP Request object. It's a Janet struct with these fields:

- :cookies
- :headers
- :path, the full path with query params
- :route, just the path, no query params
- :body, raw request body, without parsing
- :query, parsed query params into a table
- :response-headers
- :buffer
- :connection
- :data, the same as post-data
- :head-size
- :method

The other function parameter, `post-data`, is `nil` unless the user sent a POST request. If the user sent a POST request, we get that decoded into a Janet table. So a user that executes `curl -d 'one=two' <url>` will come to your post-data as `@{"one" "two"}`

The `:render-mime` can be set to `application/json` to easily transform any basic Janet data structures we return to json, so that is pretty nice.

While it hits the common parts of a web framework, HTTPF is super basic and it has some significant limitations. The big ones that stand out to me are:

At first glance, it's nifty that you get a web framework with what's basically the standard library of Janet. However, beyond very basic usage, it's not really something you can reach for.

What else is out there in the Janet ecosystem? There are two other ones that I see when searching around.  [Circlet](https://github.com/janet-lang/circlet) which, like Spork, is in the official Janet github repo. This is a library you can import, but it's on the GNU GPL license, which is an odd choice for a library, since it means you can only build GPL apps with it. I think that's a big issue for a lot of users. The other option is [Joy](https://joy.swlkr.com/) which is very nice, but has some bugs around setting cookies that I hit when playing with it. Joy is the more full featured system and it's what I used to make a little personal webapp to serve weather data.

So that's my little writeup of the HTTPF system. It might be the only tutorial out there right now. It's frustring that it doesn't do more, but Janet is a language that can continue to grow so hopefully this little framework will grow with it.