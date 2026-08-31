Issue with OneToOneField and recursive relationships in select_related() and only().

Description
In Django a 4.2 project, if you have a model with a recursive relationship
OneToOneField
like this:
class Example(models.Model):
    name = models.CharField(max_length=32)
    source = models.OneToOneField(
        'self', related_name='destination', on_delete=models.CASCADE
    )
And then query this model using:
Example.objects.select_related(
    "source",
    "destination",
).only(
    "name",
    "source__name",
    "destination__name",
).all()
It throws the following error:
django.core.exceptions.FieldError: Field Example.source cannot be both deferred and traversed using select_related at the same time.
Expected behavior:
The queryset should apply the
select_related()
and
only()
without an exception occurring as the
only()
is specifying sub fields of the fields in the
select_related()
. Or at least this is how it used to behave.
Interestingly, if you change the queryset to the following, it works without any issues:
Example.objects.select_related("source").only("name", "source__name").all()
And vice versa also works:
Example.objects.select_related("destination").only("name", "destination__name").all()
Effected versions:
This error occurs in version 4.2+ of Django.
This worked as expected in all versions of Django 4.1.
As far as I can tell, this is a regression as a brief search doesn't indicate this functionality was explicitly changed at any point. I have not tested whether this is only an issue with recursive relationships or a general issues with reverse relationships.