# django-proctor

django-proctor allows you to use [Proctor](https://github.com/indeedeng/proctor) (an A/B testing framework) from Django by using [Proctor Pipet](https://github.com/indeedeng/proctor-pipet), which exposes Proctor as a simple REST API.

Proctor allows you to place your users into randomly-assigned test groups for A/B testing. It can also be used for feature toggles and gradual rollouts of new features.

Using Proctor group assignments from Django templates is extremely easy:

```htmldjango
{% if proc.buttoncolortst.group == 'blue' %}
<button class="blue-btn"></button>
{% else %}
<button class="grey-btn"></button>
{% endif %}
```

And you can also use Proctor groups in Python code:

```py
if request.proc.newfeaturerollout.group == 'active':
    foo()
else:
    bar()
```

TODO: intro, can be used in other frameworks, required config options,
basic usage, etc.
