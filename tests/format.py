from hlib.tests import *

import hlib.format

class FormatTests(TestCase):
  def test_sanity(self):
    input = '''
An h1 header
============

Paragraphs are separated by a blank line.

2nd paragraph. *Italic*, **bold**, `monospace`. Itemized lists
look like:

  * this one
  * that one
  * the other one

Note that --- not considering the asterisk --- the actual text
content starts at 4-columns in.

> Block quotes are
> written like so.
>
> They can span multiple paragraphs,
> if you like.

Use 3 dashes for an em-dash. Use 2 dashes for ranges (ex. "it's all in
chapters 12--14"). Three dots ... will be converted to an ellipsis.



An h2 header
------------

Here's a numbered list:

 1. first item
 2. second item
 3. third item

Note again how the actual text starts at 4 columns in (4 characters
from the left side). Here's a code sample:

    # Let me re-iterate ...
    for i in 1 .. 10 { do-something(i) }

As you probably guessed, indented 4 spaces. By the way, instead of
indenting the block, you can use delimited blocks, if you like:

~~~
define foobar() {
    print "Welcome to flavor country!";
}
~~~

(which makes copying & pasting easier). You can optionally mark the
delimited block for Pandoc to syntax highlight it:

~~~python
import time
# Quick, count to ten!
for i in range(10):
    # (but not *too* quick)
    time.sleep(0.5)
    print i
~~~



### An h3 header ###

Now a nested list:

 1. First, get these ingredients:

      * carrots
      * celery
      * lentils

 2. Boil some water.

 3. Dump everything in the pot and follow
    this algorithm:

        find wooden spoon
        uncover pot
        stir
        cover pot
        balance wooden spoon precariously on pot handle
        wait 10 minutes
        goto first step (or shut off burner when done)

    Do not bump wooden spoon or it will fall.

Notice again how text always lines up on 4-space indents (including
that last line which continues item 3 above). Here's a link to [a
website](http://foo.bar). Here's a link to a [local
doc](local-doc.html). Here's a footnote [^1].

[^1]: Footnote text goes here.

Tables can look like this:

size  material      color
----  ------------  ------------
9     leather       brown
10    hemp canvas   natural
11    glass         transparent

Table: Shoes, their sizes, and what they're made of

(The above is the caption for the table.) Here's a definition list:

apples
  : Good for making applesauce.
oranges
  : Citrus!
tomatoes
  : There's no "e" in tomatoe.

Again, text is indented 4 spaces. (Alternately, put blank lines in
between each of the above definition list lines to spread things
out more.)

Inline math equations go in like so: $\omega = d\phi / dt$. Display
math should get its own line and be put in in double-dollarsigns:

$$I = \int \rho R^{2} dV$$

Done.
'''

    expected = '''<h1>An h1 header</h1>

<p>Paragraphs are separated by a blank line.</p>

<p>2nd paragraph. <em>Italic</em>, <strong>bold</strong>, <code>monospace</code>. Itemized lists
look like:</p>

<ul>
<li>this one</li>
<li>that one</li>
<li>the other one</li>
</ul>

<p>Note that --- not considering the asterisk --- the actual text
content starts at 4-columns in.</p>

<blockquote>
  <p>Block quotes are
  written like so.</p>
  
  <p>They can span multiple paragraphs,
  if you like.</p>
</blockquote>

<p>Use 3 dashes for an em-dash. Use 2 dashes for ranges (ex. "it's all in
chapters 12--14"). Three dots ... will be converted to an ellipsis.</p>

<h2>An h2 header</h2>

<p>Here's a numbered list:</p>

<ol>
<li>first item</li>
<li>second item</li>
<li>third item</li>
</ol>

<p>Note again how the actual text starts at 4 columns in (4 characters
from the left side). Here's a code sample:</p>

<pre><code># Let me re-iterate ...
for i in 1 .. 10 { do-something(i) }
</code></pre>

<p>As you probably guessed, indented 4 spaces. By the way, instead of
indenting the block, you can use delimited blocks, if you like:</p>

<p>~~~
define foobar() {
    print "Welcome to flavor country!";
}
~~~</p>

<p>(which makes copying &amp; pasting easier). You can optionally mark the
delimited block for Pandoc to syntax highlight it:</p>

<p>~~~python
import time</p>

<h1>Quick, count to ten!</h1>

<p>for i in range(10):
    # (but not <em>too</em> quick)
    time.sleep(0.5)
    print i
~~~</p>

<h3>An h3 header</h3>

<p>Now a nested list:</p>

<ol>
<li><p>First, get these ingredients:</p>

<ul>
<li>carrots</li>
<li>celery</li>
<li>lentils</li>
</ul></li>
<li><p>Boil some water.</p></li>
<li><p>Dump everything in the pot and follow
this algorithm:</p>

<pre><code>find wooden spoon
uncover pot
stir
cover pot
balance wooden spoon precariously on pot handle
wait 10 minutes
goto first step (or shut off burner when done)
</code></pre>

<p>Do not bump wooden spoon or it will fall.</p></li>
</ol>

<p>Notice again how text always lines up on 4-space indents (including
that last line which continues item 3 above). Here's a link to <a href="http://foo.bar">a
website</a>. Here's a link to a <a href="local-doc.html">local
doc</a>. Here's a footnote [^1].</p>

<p>Tables can look like this:</p>

<p>size  material      color</p>

<hr />

<p>9     leather       brown
10    hemp canvas   natural
11    glass         transparent</p>

<p>Table: Shoes, their sizes, and what they're made of</p>

<p>(The above is the caption for the table.) Here's a definition list:</p>

<p>apples
  : Good for making applesauce.
oranges
  : Citrus!
tomatoes
  : There's no "e" in tomatoe.</p>

<p>Again, text is indented 4 spaces. (Alternately, put blank lines in
between each of the above definition list lines to spread things
out more.)</p>

<p>Inline math equations go in like so: $\omega = d\phi / dt$. Display
math should get its own line and be put in in double-dollarsigns:</p>

<p>$$I = \int 
ho R^{2} dV$$</p>

<p>Done.</p>
'''

    EQ(expected, hlib.format.tagize(input))
