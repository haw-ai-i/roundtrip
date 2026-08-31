Error with decode_unicode=True on streamed response
With `requests==2.11.0` I get `AttributeError: 'NoneType' object has no attribute 'readline'` when trying to use `iter_lines` with `decode_unicode=True` on a streamed response.

``` sh
$ ./bin/pip freeze
requests==2.11.0
wsgiref==0.1.2
```

``` python
from contextlib import closing
import requests


with closing(requests.get('http://httpbin.org/stream/20', stream=True)) as response:
    for line in response.iter_lines(chunk_size=30, decode_unicode=True):
        print line
```

``` python
$ ./bin/python case.py

Traceback (most recent call last):
  File "case.py", line 6, in <module>
    for line in response.iter_lines(chunk_size=30, decode_unicode=True):
  File "/Users/jone/temp/requests-stream/lib/python2.7/site-packages/requests/models.py", line 720, in iter_lines
    for chunk in self.iter_content(chunk_size=chunk_size, decode_unicode=decode_unicode):
  File "/Users/jone/temp/requests-stream/lib/python2.7/site-packages/requests/utils.py", line 374, in stream_decode_response_unicode
    for chunk in iterator:
  File "/Users/jone/temp/requests-stream/lib/python2.7/site-packages/requests/models.py", line 676, in generate
    for chunk in self.raw.stream(chunk_size, decode_content=True):
  File "/Users/jone/temp/requests-stream/lib/python2.7/site-packages/requests/packages/urllib3/response.py", line 353, in stream
    for line in self.read_chunked(amt, decode_content=decode_content):
  File "/Users/jone/temp/requests-stream/lib/python2.7/site-packages/requests/packages/urllib3/response.py", line 521, in read_chunked
    line = self._fp.fp.readline()
AttributeError: 'NoneType' object has no attribute 'readline'
```

When removing either `stream=True` or `decode_unicode=True` the script works well.

This issue may be related to #3174.

