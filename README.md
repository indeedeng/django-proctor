# django-proctor

![OSS Lifecycle](https://img.shields.io/osslifecycle/indeedeng/django-proctor.svg)

django-proctor allows you to use [Proctor](https://github.com/indeedeng/proctor) (an A/B testing framework) from Django by using [Proctor Pipet](https://github.com/indeedeng/proctor-pipet), which exposes Proctor as a simple REST API.

Proctor allows you to place your users into randomly-assigned test groups for A/B testing. It can also be used for feature toggles and gradual rollouts of new features.

Using Proctor group assignments from Django templates is extremely easy by checking the bucket's name:

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

If you need to use Proctor groups in a cron job or some service without a request, you can do an Account test:
```py
from proctor.identify import proc_by_accountid

accountid = 999999
if proc_by_accountid(accountid).newfeaturerollout.group == "active":
    foo()
else:
    bar()

```

## Configuration

Before using django-proctor, you need to set up [Proctor Pipet](https://github.com/indeedeng/proctor-pipet). This is the REST API that django-proctor communicates with to obtain test group assignments.

You'll also need a test matrix, which defines all Proctor tests and their current allocations. [Proctor Webapp](https://github.com/indeedeng/proctor-webapp) provides a way to view and modify the test matrix.

### Requirements

To use django-proctor, just install it with pip:

```bash
$ pip install django-proctor
```

Or add it to your `requirements.txt` file (preferably with the current version).

### Views

There are a set of private views that are available for testing and debugging. Enabling these views requires some extra configuration.

#### Installed Apps

Add `proctor` to your project's list of installed apps.

```py
INSTALLED_APPS += (
    ...
    proctor,
    ...
)
```
#### Urls

Import the proctor urls into a private space in your project.

```py
urlpatterns = [
    ...
    url(r'^private/', include('proctor.urls'))
    ...
]
```

##### ShowTestMatrix

The ShowTestMatrix view allows you to see the entire test matrix for your specific PROCTOR_TESTS. This view is simply the json version of the test matrix filtered to your tests.


Using the above url pattern example, the test matrix would be available at `http://<your_project_root>/private/proctor/show` and `http://<your_project_root>/private/showTestMatrix`. The latter is for backwards compatibility with other projects.

##### Force Groups

The Force Groups view allows you to see what the current group assignments are for your session and identification and force yourself into a specific group for any test.

**NOTE**: This template does come with a default base template, but it can be overidden. To override the default base template, you must have a base template to extend and the name of that template file should be set in PROCTOR_BASE_TEMPLATE.

Using the above url pattern example, the force groups page would be available at `http://<your_project_root>/private/proctor/force`.

### Middleware

django-proctor does most of its processing in a middleware. This runs before your views and adds `proc` to the `request` object, which lets you access test group assignments.

You must subclass `proctor.middleware.BaseProctorMiddleware` and override several functions to provide django-proctor with information it needs to handle group assignments.

```py
class MyProctorMiddleware(proctor.middleware.BaseProctorMiddleware):
    ...
```

#### get_identifiers()

Identifiers are strings that identify users of your site uniquely. These can include tracking cookies and account ids. Proctor uses this information to keep users in the same test groups across requests.

This returns a dict of identifier source keys (see Pipet configuration) to their values.

If a user lacks a certain identifier, don't include it in the dict. Proctor will skip any tests using that identifier. However, make sure you always return at least one identifier like a tracking cookie.

You **must** override this method.

This method is always run after any previous middleware.

```py
def get_identifiers(self, request):
    ids = {'USER': request.COOKIES.get('tracking')}

    if request.user.is_authenticated:
        ids['acctid'] = request.user.id

    return ids
```

#### get_context()

Context variables are properties about the user that are used in Proctor test rules to selectively enable tests or change the allocations of a test depending on whether an expression is true. This can be used to run a test only on Firefox, or you can run a test at 50% for US users and 10% for everyone else.

This returns a dict of context variable source keys (see Pipet configuration) to their values, which are converted by Pipet to their final types before rule expressions are evaluated.

If you don't override this method, django-proctor uses no context variables.

If the Pipet configuration doesn't have a default value for a context variable, it must be included on every API request. If that is the case, make sure that context variable appears in this return value.

This method is always run after any previous middleware.

```py
def get_context(self, request):
    return {"ua": request.META.get('HTTP_USER_AGENT', ''),
            "loggedIn": request.user.is_authenticated,
            "country": geo.country(request.get_host()),
    }
```

#### is_privileged()

Returns a bool indicating whether the request is allowed to use the `prforceGroups` query parameter to force themselves into Proctor groups.

If you don't override this method, it returns False, which effectively disables force groups.

Use something like IP address or admin account to determine whether the user can force themselves into test groups.

This method **may** run without hitting any of the previous middleware. You must assume anything that may have been done in a middleware, like adding a `user` attribute to `request`, may not have happened. Otherwise, you might get exceptions in strange conditions like redirects.

```py
def is_privileged(self, request):
    return (request.get_host().startswith('127.0.0.1') or
            request.get_host().startswith('192.168.') or
            (hasattr(request, 'user') and request.user.is_staff)
    )

```

#### get_http()

Returns an instance of `requests.Session` (or equivalent) that will be used when making HTTP requests to the API.

If you don't override this method, it returns None, which will cause the api to use the `requests` module.

### settings.py

You must set several things in your `settings.py` for django-proctor to work properly:

#### MIDDLEWARE

Add the middleware you created to `MIDDLEWARE`. Make sure you place it after any middleware it depends on like `AuthenticationMiddleware`.

#### TEMPLATE_CONTEXT_PROCESSORS

Add `proctor.context_processors.proc` to `TEMPLATE_CONTEXT_PROCESSORS`. This makes the `proc` object available in all of your Django templates.

#### PROCTOR_API_ROOT

Set `PROCTOR_API_ROOT` to the URL at which Proctor Pipet is running.

Include `http://` or `https://`. Do not include a trailing slash.

If you want production to use a different test matrix than your staging server and your developer machines, then you may want to use a different Pipet instance depending on environment.

```py
PROCTOR_API_ROOT = "http://pipet.example.com"
```

#### PROCTOR_TESTS

`PROCTOR_TESTS` is a tuple or list of the Proctor tests that your Django project intends to use.

Add tests to this tuple before implementing them in your templates and code, and remove tests from this tuple after removing their implementations.

All tests listed here are guaranteed to exist on the `proc` object.

The tests listed here will also be in `str(proc)` (for logging test groups) if they have non-negative group values.

```py
PROCTOR_TESTS = (
    'buttoncolortst',
    'newfeaturerollout',
)
```

If you're only using one test, make sure you include a comma in the tuple. Otherwise, Python interprets it as just a string.

```py
PROCTOR_TESTS = ('buttoncolortst',)
```

#### PROCTOR_BASE_TEMPLATE

Set `PROCTOR_BASE_TEMPLATE` to the name of the base html template being used in your project.

```py
PROCTOR_BASE_TEMPLATE = "base.html"
```

#### PROCTOR_CACHE_METHOD

You can optionally have django-proctor cache group assignments from the Proctor Pipet REST API. Ordinarily, every HTTP request that hits Django will trigger the Proctor middleware to make an HTTP request to Pipet. You can use caching to avoid this extra cost since group assignments typically stay the same.

If the cache has no useful value (like when a new user visits your site), then django-proctor falls back to making an HTTP request to Proctor Pipet.

If `PROCTOR_CACHE_METHOD` is missing or None, django-proctor will not do any caching.

If `PROCTOR_CACHE_METHOD` is `'cache'`, django-proctor uses [Django's cache framework](https://docs.djangoproject.com/en/dev/topics/cache/) for caching group assignments. See `PROCTOR_CACHE_NAME`.

If `PROCTOR_CACHE_METHOD` is `'session'`, django-proctor caches group assignments in the `request.session` dict. This is a decent option if all of your HTTP requests get or set [Django's session object](https://docs.djangoproject.com/en/dev/topics/http/sessions/) anyway.

##### Cache Invalidation

django-proctor's cache invalidation is fairly smart and will not use the cache if some property of the user's request has changed, like the identifiers, context variables, or the `prforceGroups` parameter. The cache will also be ignored if you change a setting like `PROCTOR_API_ROOT` or `PROCTOR_TESTS`.

This means that if a user logs in, or a user changes their useragent, or you add a new test to `PROCTOR_TESTS`, the cached value will be skipped. You don't have to worry about outdated values.

**TODO: Explain matrix version detection and caching after that invalid cache issue is resolved. Current cache implementation does not work properly with multiple processes.**

#### PROCTOR_CACHE_NAME

This setting is only meaningful if `PROCTOR_CACHE_METHOD` is `'cache'`.

`PROCTOR_CACHE_NAME` is the name of a cache in `CACHES` that django-proctor will use.

If `PROCTOR_CACHE_NAME` is missing or None, django-proctor uses the `default` cache.

#### PROCTOR_LAZY

If `PROCTOR_LAZY` is `True`, then the `proc` object lazily loads its groups. Proctor group assignments are only retrieved from either the cache or the Proctor Pipet REST API on first access of the `proc` object.

This means that HTTP requests to your Django server that never use the `proc` object don't incur the cost of getting group assignments.

When measuring performance, remember that this option may move the timing of a cache access and REST API request to an unexpected place (like during template rendering).

If `PROCTOR_LAZY` is missing or `False`, lazy loading will not be used.

## Usage

The Proctor middleware adds a `proc` object to `request`, which allows you to easily use Proctor group assignments from any view.

Group assignments can be accessed using the dot operator on `proc`. Every test listed in `PROCTOR_TESTS` is guaranteed to exist as an attribute on `proc`.

```py
print request.proc.buttoncolortst
# -> GroupAssignment(group=u'blue', value=1, payload=u'#2B60DE')

print request.proc.testnotinsettings
# throws AttributeError
```

Each group assignment has three attributes:

* **group**: the assigned test group name (str)
* **value**: the assigned bucket value (int)
    * -1 typically means inactive, and 0 typically means control.
* **payload**: the assigned test group payload value
    * Used to change test-specific values from Proctor instead of in code.
    * Is `None` if the test has no payload.
    * The payload type can be a str, long, double, or a list of one of those.

If Proctor did not give an assignment for a test, then that test is unassigned. In that case: group, value, and payload are all `None`.

```py
print request.proc.buttoncolortst
# -> GroupAssignment(group=None, value=None, payload=None)
```

This can happen if an eligibility rule was not met, if there was no matching identifier for the test type, if the test was in `PROCTOR_TESTS` but not in the test matrix, or if django-proctor could not connect to Pipet (or got back an HTTP error) and set all assignments to unassigned by default.

### Switching

You can use Proctor group assignments to implement different behavior on your site based on the user's assigned test group.

Suppose we have a test called "algorithmtst" in our test matrix with four test groups: `'inactive'`, `'control'`, `'bogo'`, and `'quick'`:

```py
if request.proc.algorithmtst.group == 'bogo':
    bogosort()
elif request.proc.algorithmtst.group == 'quick':
    quicksort()
else:
    # 'control', 'inactive', and None (all default to our old sorting algorithm)
    # Because this covers None (unassigned), this will also be used in case of error.
    oldsort()
```

Usually your `'control'`, `'inactive'`, and `None` groups will have the same behavior, which is doing whatever your site did before you added this test or feature. It's convenient to have the else branch cover all of these groups.

Ensure that your branches always cover the case that group is `None`. This ensures that if your Proctor Pipet instance goes down or starts returning an HTTP error due to some misconfiguration, your site will simply fall back to default behavior.

### Templates

Proctor can be used from Django templates as well if you properly set up `TEMPLATE_CONTEXT_PROCESSORS`.

Your templates have the `proc` object in their context, allowing you to switch behavior based on Proctor groups:

```htmldjango
{% if proc.buttoncolortst.group == 'blue' %}
<button class="blue-btn"></button>
{% elif proc.buttoncolortst.group == 'green' %}
<button class="green-btn"></button>
{% else %}
<button class="grey-btn"></button>
{% endif %}
```

```htmldjango
{% if proc.newfeaturerollout.group == 'active' %}
<button>Try our new feature!</button>
{% endif %}
```

### Payloads

Payloads allow you to specify test-specific values in the test matrix instead of in your code. This allows you to try many different variations without touching Django or even redeploying your application.

Here is an example for button text on a call to action:

```htmldjango
<button>{{ proc.buttontexttst.payload|default_if_none:"Sign Up" }}</button>
```

Remember that payload can be `None` in many cases, including if Proctor Pipet goes down. Include a [default_if_none](https://docs.djangoproject.com/en/dev/ref/templates/builtins/#default-if-none) filter to ensure rational default behavior if this happens.

Payloads can also be used from your views:

```py
algorithm_constants = request.proc.algoconsttst.payload
if algorithm_constants is None:
    algorithm_constants = [2, 3, 42]

search_ranking(algorithm_constants)
```

#### Payload Arrays

`payload` is `None` when a test group is unassigned, so any attribute accesses are still an error.

In Python code, make sure you check for `None` before accessing attributes on the payload.

In Django template output tags, invalid attribute accesses are interpreted as the `TEMPLATE_STRING_IF_INVALID` setting, which is the blank string by default. You can use the [default](https://docs.djangoproject.com/en/dev/ref/templates/builtins/#default) template tag to cover these instances, but be aware that this will also match on empty arrays and other falsey values:

```htmldjango
<h1>{{ proc.headertexttst.payload.0|default:"Default Title" }}</h1>
<p>{{ proc.headertexttst.payload.1|default:"Default description text." }}</p>
```

See [How invalid variables are handled](https://docs.djangoproject.com/en/dev/ref/templates/api/#invalid-template-variables) in the Django template documentation for more details.

### JavaScript

If you want to use Proctor test group assignments from browser-side JavaScript, you'll have to provide the values you want to use to your JavaScript through Django's templating language.

A simple way to do this is to define global JavaScript variables in a script tag in your HTML template with the values your code will use:

```htmldjango
<script type="text/javascript">
    {% if proc.buttoncolortst.group is not None %}
    var buttoncolortstgroup = "{{ proc.buttoncolortst.group|escapejs }}";
    {% else %}
    var buttoncolortstgroup = null;
    {% endif %}

    {% if proc.newfeaturerollout.group == 'active' %}
    var usenewfeature = true;
    {% else %}
    var usenewfeature = false;
    {% endif %}

    var buttontext = "{{ proc.buttontexttst.payload|default_if_none:"Sign Up"|escapejs }}";
</script>
```

For strings, wrap the template output tag in quotes. Use the [escapejs](https://docs.djangoproject.com/en/dev/ref/templates/builtins/#escapejs) filter so that special characters like quotes and angle brackets are correctly placed into your JavaScript.

Some people place script tags like this in a template block like "js" so that these special values appear in a consistent place alongside other script includes.

You can use these global variables in your JavaScript static files to implement your tests:

```js
$(function() {
    if (buttoncolortstgroup === "blue") {
        $(".buttonone").css("background", "#00f");
    } else if (buttoncolortstgroup === "green") {
        $(".buttonone").css("background", "#0f0");
    } else {
        $(".buttonone").css("background", "#888");
    }

    if (usenewfeature) {
        $(".buttontwo").show();
    }

    $(".buttonthree").text(buttontext);
});
```

This is just one way of accessing Proctor test groups from the browser. Use whatever makes the most sense for your project.

Another way is templating your JavaScript directly by placing your code in HTML and mixing your Django template tags with JavaScript code. You could even template your .js files instead of serving them statically. However, these two alternatives can be messy and are not best practices.

If your application is complex enough, you could even consider making a Django view that returns some test groups or payloads and have your JavaScript make an AJAX request to get them.

### Logging

To compare metrics between two different test groups, you can log each request's assigned test groups in addition to any metrics you want to track.

django-proctor provides a simple comma-separated representation of all the Proctor test groups that the user is in for logging purposes:

```py
print str(request.proc)
# -> "buttoncolortst1,countryalgotst0,newfeaturerollout0"
```

This output only includes non-negative test groups, as -1 typically means inactive groups that should not be logged.

The `proc` object also has a method to obtain the list of test groups before joining with a comma:

```py
print request.proc.get_group_string_list()
# -> ['buttoncolortst1', 'countryalgotst0', 'newfeaturerollout0']
```

### prforceGroups

To test the implementation of your test group behavior, privileged users can attach a `prforceGroups` query parameter to their site's URL to force themselves into certain test groups:

```
http://django.example.com/?prforceGroups=buttoncolortst2,countryalgotst0
```

The format is simply the test name followed by the bucket value (not the name), with all test groups separated by commas.

The value of `prforceGroups` is set as a session cookie. Your browser will be forced into those groups until your browser is closed. You can also set an empty prforceGroups to clear the cookie:

```
http://django.example.com/?prforceGroups=
```

The tests and bucket values specified in `prforceGroups` must exist in the Proctor test matrix.

## Using Proctor from Other Python Frameworks

django-proctor was designed primarily for Django as that is the framework that we (the Indeed Labs team) primarily use.

However, these modules would be usable in other Python frameworks with some minor modifications:

`api`, `cache*`, `groups`, `identify`, `lazy`

cache unfortunately has some Django mixed in for some of its subclasses. It imports django.core.cache, it uses Django in subclasses, and the abstract Cacher interface takes `request` as a parameter (because `SessionCacher` needs it, but it can safely be None for all other subclasses).

Also, identify.py imports from django settings for similar reasons when looking up account details.

If this is a significant problem for you, ask us to split this into two packages: one for Python, and one for Django that has the former as a dependency. Or contribute a solution that splits the packages up.

When implementing Proctor in other frameworks, use `middleware.py` to see how we implemented this for Django. We handle providing context variables and identifiers through subclassing. Other implementations could register functions (through decorators or otherwise) to provide these details. Also, note how the prforceGroups query parameter and cookie is handled.


## Testing

This project uses [`tox` for executing tests](https://tox.readthedocs.io/en/latest/). To run tests
locally, cd into your project and run

    $ tox

Underneath the hood, `tox` is just running
[`pytest` for test discovery and execution](https://docs.pytest.org/en/latest/). Test arguments can
be passed through into `pytest` by adding `--` after your `tox` command. For example, you can
isolate a test file or test method using the following:

    $ tox -- proctor/tests/test_identify.py
    $ tox -- proctor/tests/test_identify.py::TestIdentifyGroups::test_requested_group_resolved

where `pytest` uses a double colon as a test class/method/function separator

By default, `pytest` captures output, which prevents debugging with breakpoints. If you need to
debug the tests, you can run either of the following:

    $ tox -- --capture=no
    $ tox -- -s

You can then add a break point to a test by adding the following to your python code:

```python
import pdb; pdb.set_trace()
```


## See Also

* [Proctor Pipet](https://github.com/indeedeng/proctor-pipet)

* [Proctor Documentation](http://indeedeng.github.io/proctor/)

* [Proctor Github Repo](https://github.com/indeedeng/proctor)

* [Proctor Webapp](https://github.com/indeedeng/proctor-webapp) for editing the test matrix.

* [indeedeng-proctor-users](https://groups.google.com/forum/#!forum/indeedeng-proctor-users) for questions and comments.

* [Proctor Blog Post](http://engineering.indeed.com/blog/2014/06/proctor-a-b-testing-framework/) on the Indeed Engineering blog.

* [Proctor Tech Talk](http://engineering.indeed.com/talks/managing-experiments-behavior-dynamically-proctor/)

## Code of Conduct
This project is governed by the [Contributor Covenant v 1.4.1](CODE_OF_CONDUCT.md)

## License
This project uses the [Apache 2.0](LICENSE.txt) license.
