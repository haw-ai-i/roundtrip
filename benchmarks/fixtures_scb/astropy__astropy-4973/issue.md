Don't raise an error if passing zero coordinates to WCS
Currently, passing a (0,2) shaped array to the WCS transformation functions raises an error:

```
In [5]: wcs.wcs_world2pix(np.zeros((0,2)),0)
---------------------------------------------------------------------------
InconsistentAxisTypesError                Traceback (most recent call last)
<ipython-input-5-ef859a33e63b> in <module>()
----> 1 wcs.wcs_world2pix(np.zeros((0,2)),0)

/Users/tom/miniconda3/envs/dev35/lib/python3.5/site-packages/astropy/wcs/wcs.py in wcs_world2pix(self, *args, **kwargs)
   2159         return self._array_converter(
   2160             lambda xy, o: self.wcs.s2p(xy, o)['pixcrd'],
-> 2161             'input', *args, **kwargs)
   2162     wcs_world2pix.__doc__ = """
   2163         Transforms world coordinates to pixel coordinates, using only

/Users/tom/miniconda3/envs/dev35/lib/python3.5/site-packages/astropy/wcs/wcs.py in _array_converter(self, func, sky, *args, **kwargs)
   1247             if self.naxis == 1 and len(xy.shape) == 1:
   1248                 return _return_list_of_arrays([xy], origin)
-> 1249             return _return_single_array(xy, origin)
   1250 
   1251         elif len(args) == self.naxis + 1:

/Users/tom/miniconda3/envs/dev35/lib/python3.5/site-packages/astropy/wcs/wcs.py in _return_single_array(xy, origin)
   1231             if ra_dec_order and sky == 'input':
   1232                 xy = self._denormalize_sky(xy)
-> 1233             result = func(xy, origin)
   1234             if ra_dec_order and sky == 'output':
   1235                 result = self._normalize_sky(result)

/Users/tom/miniconda3/envs/dev35/lib/python3.5/site-packages/astropy/wcs/wcs.py in <lambda>(xy, o)
   2158             raise ValueError("No basic WCS settings were created.")
   2159         return self._array_converter(
-> 2160             lambda xy, o: self.wcs.s2p(xy, o)['pixcrd'],
   2161             'input', *args, **kwargs)
   2162     wcs_world2pix.__doc__ = """

InconsistentAxisTypesError: ERROR 4 in wcss2p() at line 2876 of file cextern/wcslib/C/wcs.c:
ncoord and/or nelem inconsistent with the wcsprm.
```

It might be nice to simply return a new array with the same size? I ran across this in WCSAxes (I don't control what N is going to be in advance since it depends on the calculation for the grid lines, and sometimes it just happens N is zero).

