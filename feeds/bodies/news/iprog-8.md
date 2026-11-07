Page 1 of 3If jQuery doesn't do what you want then make it so by writing a plugin - it is suprisingly easy. This is an exclusive extract from Ian Elliot's new book on jQuery 4.

## Programmer**’s Guide To** jQuery 4

#### By Ian Elliot

[](<https://www.amazon.com/dp/1871962684?_encoding=UTF8&qid=&sr=&linkCode=ll1&tag=iprog-20&linkId=13e3793e24ef8654297f065cab51686a&language=en_US&ref_=as_li_ss_tl>)

#### Contents****

  1. **Understanding jQuery**
  2. **Working With The DOM  
** Extract: [Basic DOM](<https://www.i-programmer.info/programming/207-jquery/18832-jquery-4-basic-dom.html>)****
  3. **Mastering Selectors: Finding Elements  
**Extract: [Basic Selectors](<https://www.i-programmer.info/programming/207-jquery/18976-jquery-4-basic-selectors.html>)********
  4. [The jQuery Object](<https://www.i-programmer.info/programming/207-jquery/18876-jquery-4-the-jquery-object.html>)****
  5. **Mastering Selectors: Filters  
** Extract:****[Filters](<https://www.i-programmer.info/programming/207-jquery/19034-jquery-4-filters.html>)
  6. **Traversal Filters**
  7. **Modifying DOM Objects  
** Extract: [Modifying DOM Objects](<https://www.i-programmer.info/programming/207-jquery/19134-jquery-4-modifying-dom-objects.html>)
  8. **Creating Objects & Modifying The DOM Hierarchy **
  9. **Working With Data**
  10. **Forms**
  11. **Function Queues**
  12. **Animation**
  13. [Reinventing Events](<https://www.i-programmer.info/programming/113-javascript/18770-jquery-4-reinventing-events.html>)****
  14. **Working With Events**
  15. **AJAX Basics – Get**
  16. **AJAX Basics – POST**
  17. **Sending Data To The Server**
  18. **Sending Data To The Client**
  19. **JSONP For Transport**
  20. **The jqXHR Object**
  21. **Character Encoding**
  22. [jQuery 4 - Plugins](<https://www.i-programmer.info/programming/207-jquery/19260-jquery-4-plugins.html>) *********NEW!******

<ASIN:187196248X> There comes a point in every jQuery programmer's life when they look at some JavaScript they have just created and realize that it is time to integrate it with jQuery – in short create a plugin. It turns out to be easier than you might expect!  Plugins are simple ways to extend what jQuery does. If you create your plugin correctly then you will get the additional benefits of being more closely integrated with jQuery. In particular, you can make your new facility work with jQuery chaining so that it can be part of a longer sequence of commands. For the sake of an example, let's return to the table-generating function created in Chapter 8:

    function table(n, m) { 
     var table = $("<table>"); 
     var tbody = $("<tbody>"); 
     var row = $("<tr>"); 
     var cell = $("<td>"); 
     for (var i = 0; i < n; i++) { 
      var tempRow = row.clone(); 
      for (var j = 0; j < m; j++) {
       tempRow.append(cell.clone().html(i+","+j));
      } 
      tbody.append(tempRow); 
     } 
     table.append(tbody); 
     return table; 
    }

This builds a table element with n rows and m columns which it returns as the result of the function. This is really far too simple to integrate into jQuery, but imagine that it has lots of extra facilities implemented as properties and methods.

## The Basic Plugin

A plugin is just a function – one function is one plugin and, to keep things simple, you should try to include as much functionality as possible within each plugin rather than pollute the jQuery namespace with multiple functions. To add your function to jQuery all you have to do is create a new property on jQuery.fn:

    jQuery.fn.myFunction= function definition

_or:_

    _$.fn.myFunction= function definition_

After this you can use your function with the usual jQuery syntax:

    $().myFunction();

This is almost too easy! If you want to fully understand what is going on then you need a little more explanation. However, if you don't want to know then skip to the next section. The first question is, why do we assign our new method to _jQuery.fn_ and not directly to jQuery, which is the object we are extending? The answer is subtle. The jQuery object that you usually reference with _$_ is just a constructor function for the _jQuery_ function object that you actually use to get things done. Hence the j _Query.prototype_ property can be used to set all of the default properties for the jQuery function object that you use. That is: $.fn is simply an alias for jQuery.prototype. When you add a method here, you are making it available to every instance of a jQuery object (the objects returned by the $(selector) call). So, to add to the jQuery function object you simply add to _jQuery.fn_ , which is set up in the jQuery code to point to the same object as the prototype. After you have added your new function, if you cannot use:

    $.myFunction();

as this will generate an error that jQuery doesn't have a _myFunction_ property. However:

    $().myFunction();

works because $() acts as the constructor for the jQuery function object which is returned in the usual way and this does have a _myFunction_ property via the prototype mechanism. This is subtle and you need to refresh how JavaScript inheritance works if you find it puzzling. If you do want to add a property to the constructor then you add it directly. For example:

    $.myFunction2 = function() {...};

adds the _myFunction2_ property to the jQuery constructor, not to the jQuery function object. Following this you can call _myFunction2_ as:

    $.myFunction2();

as it is a method of the jQuery constructor, but not as:

    $().myFunction2();

as it is not a property of the jQuery function object. When should you add a property directly to the constructor (`$.myFunction`) rather than the prototype (`$.fn.myFunction`)? The answer is simple: use the **constructor** if your plugin doesn't need to operate on a set of selected DOM elements. These are often called "utility" functions. By adding the property to the constructor, you make it clear that the function is a standalone tool. Following this logic, you cannot use selectors with:

    $.myFunction2() 

But you can(and usually should) with:

    $(selectors).myFunction2();

As already mentioned, you don't need to know this to add a new plugin, but it is interesting and might even help you with debugging if anything goes wrong.