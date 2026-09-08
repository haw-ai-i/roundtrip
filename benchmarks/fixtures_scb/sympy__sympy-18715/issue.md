Cannot modify MutableDenseNDimArray
Hello,

My understanding is that you should be able to modify the values in a MutableDenseNDimArray, however, since the update to version 1.5, I have not been able to do so.

Minimal working example:

`import sympy`
`p = sympy.MutableDenseNDimArray.zeros(3)`
`p[0] = 5`

The above code gives the following error: "ValueError: Only a tuple index is accepted"

I've tried searching for information on this error, but I can't find anything. The above code works in version 1.4.
