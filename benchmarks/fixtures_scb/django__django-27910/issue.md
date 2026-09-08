Allow using an Enum class in model Field choices

Description
I will simply stick to your example here:
​
https://docs.djangoproject.com/en/dev/ref/models/fields/#choices
I want to limit the input to certain choices so I create a list/tuple of tuples/lists. Since Python 3.4 there is a class called
​
Enum
and some nice decorators like
​
@unique
.
Currently, if you want to use this you have to do 1/2 dirty hacks, descriped in
​
this article
, which I would prefer over the current solution.
It would be nice to have native support for the Enum class, e.g. you can directly pass the class to choices (instead of using the class method choices() ), also when refering to an element in the enum just using
Student.Freshmann
instead of
Student.Freshmann.value
A simple example would be this:
from enum import Enum

class Student(models.Model):
    class YearInSchoolChoices(Enum):
        Freshman = 'FR'
        Sophomore = 'SO'
        Junior = 'JR'
        Senior = 'SR'
    
    year_in_school = models.CharField(
        max_length=2,
        choices=YearInSchoolChoices,
        default=YearInSchoolChoices.Freshman,
    )

    def is_upperclass(self):
        return self.year_in_school in (self.YearInSchoolChoices.Junior, self.YearInSchoolChoices.Senior)
Also this could be adopted (if accepted) to any type of choices in django, e.g.
​
Choicefield
etc.