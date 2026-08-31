HTML class for non-field errors

Description
In most of my applications I like field errors and non-field errors to display slightly differently. In general I need field errors to line up with the field or use an icon to indicate which field they correspond to (such as an arrow icon). Non-field errors of course can't have an arrow icon and don't line up with fields (ie. need different margins).
At the moment it's difficult to arrange this without extra markup, because it's usually hard to write a CSS selector that selects only field xor non-field errors.
It would be really helpful if the output was, say,
<ul class="errorlist nonfielderrorlist">
when rendering
form.non_field_errors
.