BaseFormSet's empty_form isn't as extendable as _construct_form()

Description
It is possible to wedge extra kwargs into each form in a Formset by doing something like:
class MyFormSet(BaseFormSet):
    def _construct_form(self, i, **kwargs):
        kwargs['extrafield'] = 1
        return super(MyFormSet, self)._construct_form(i, **kwargs)
which is useful for forms wanting to require additional arguments - for inlines wanting to act on values in an existing parent instance, for example.
However, the kwarg can't be required, because of the empty_form property, which doesn't have any way of marshall extra kwargs to the form (though it can add fields), as such, the empty_form definition must be copy-pasted entirely, which isn't ideal if the definition upstream (ie: in Django) shifts over time.
A private api method:
def _get_empty_form_kwargs(self):
    return {}
which could be dictionary expanded into the empty_form would allow for passing required arguments in [I believe] a backwards compatible way, while allowing userland code to replace less of the core FormSet functionality.
The final empty_form might be something like:
@property
    def empty_form(self):
        form = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
            **self._get_empty_form_kwargs(),
        )
        self.add_fields(form, None)
        return form