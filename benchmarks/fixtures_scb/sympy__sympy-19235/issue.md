Respect `inv_trig_style` in inverse hyperbolic trig functions
Upstreamed from the galgebra printer, which seemed to want these.

<!-- Your title above should be a short description of what
was changed. Do not include the issue number in the title. -->

#### References to other Issues or PRs
<!-- If this pull request fixes an issue, write "Fixes #NNNN" in that exact
format, e.g. "Fixes #1234" (see
https://tinyurl.com/auto-closing for more information). Also, please
write a comment on that issue linking back to this pull request once it is
open. -->
Follows on from gh-14774

#### Brief description of what is fixed or changed

`latex(acosh(x), inv_trig_style="power")` now gives a result including `cosh^{-1}`.

#### Other comments

Upstreamed from galgebra, https://github.com/pygae/galgebra/blob/master/galgebra/printer.py#L830

#### Release Notes

<!-- Write the release notes for this release below. See
https://github.com/sympy/sympy/wiki/Writing-Release-Notes for more information
on how to write release notes. The bot will check your release notes
automatically to see if they are formatted correctly. -->

<!-- BEGIN RELEASE NOTES -->
* printing
  * the inverse hyperbolic functions now respect the `inv_trig_style` printer setting
