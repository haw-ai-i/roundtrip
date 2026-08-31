Update Legend draggable API
## PR Summary

As proposed in the discussion of #9181 this implements `Legend.set_draggable` and `Legend.get_draggable`. It also deprecates `Legend.draggable()` in favor of the former.

Note: I was not able to provide a reasonable docstring for the parameter `use_blit`. Apart from guessing that this means bit blit is somehow used when rendering the legend during drawing, I couldn't provide any useful hint to the user, even with looking deeper into the code. Blit is thoroughly undocumented throughout the code. Ideas for a useful docstring are welcome.

## PR Checklist

- [x] Code is PEP 8 compliant
- [x] Documentation is sphinx and numpydoc compliant
- [x] Documented in doc/api/api_changes.rst if API changed in a backward-incompatible way

