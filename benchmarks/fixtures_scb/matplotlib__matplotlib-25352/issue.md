MNT: Use WeakKeyDictionary and WeakSet in Grouper
## PR Summary

Rather than handling the weakrefs ourselves, just use the builtin WeakKeyDictionary and WeakSet instead. This will automatically remove dead references meaning we can remove the clean() method.

Follow-up from: #25332

## PR Checklist

<!-- Please mark any checkboxes that do not apply to this PR as [N/A]. -->

**Documentation and Tests**
- [-] Has pytest style unit tests (and `pytest` passes)
- [x] Documentation is sphinx and numpydoc compliant (the docs should [build](https://matplotlib.org/devel/documenting_mpl.html#building-the-docs) without error).
- [-] New plotting related features are documented with examples.

**Release Notes**
- [-] New features are marked with a `.. versionadded::` directive in the docstring and documented in `doc/users/next_whats_new/`
- [-] API changes are marked with a `.. versionchanged::` directive in the docstring and documented in `doc/api/next_api_changes/`
- [x] Release notes conform with instructions in  `next_whats_new/README.rst` or `next_api_changes/README.