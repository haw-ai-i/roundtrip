ForeignKey with m2m filter can duplicate foreign model entries in ModelForm/ModelChoiceField

Description
My app has the following models similar to:
PROXY_GROUPS
=
(
'Terminal Server'
,
'Socks Proxy'
,
'Web Proxy'
)
class
Group
(
models
.
Model
):
name
=
models
.
CharField
(
maxlength
=
32
)
class
Asset
(
models
.
Model
):
name
=
models
.
CharField
(
maxlength
=
32
)
groups
=
models
.
ManyToManyField
(
Group
)
class
Proxy
(
models
.
Model
):
asset
=
models
.
ForeignKey
(
Asset
,
limit_choices_to
=
{
'groups__name__in'
:
PROXY_GROUPS
,
'distinct'
:
True
})
port
=
models
.
PositiveIntegerField
()
Which spews an error when I try to add a Proxy object in the admin. The error is something to do with 'distinct' not being a valid field (Sorry i can post the exact error later).
How can I achieve the equivalent to this in the current post-mr trunk?
From #django earlier today:
malcolmt	mattimustang_: I think you've found a bug. You're right, distinct has become a method on QuerySets, not a filter parameter now. So you may be temporarily stuck. Can you file a ticket so we don't forget to fix this somehow, please?