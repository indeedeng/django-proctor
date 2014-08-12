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

## Configuration

Before using django-proctor, you need to set up [Proctor Pipet](https://github.com/indeedeng/proctor-pipet). This is the REST API that django-proctor communicates with to obtain test group assignments.

You'll also need a test matrix, which defines all Proctor tests and their current allocations. [Proctor Webapp](https://github.com/indeedeng/proctor-webapp) provides a way to view and modify the test matrix.

### Requirements

To use django-proctor, just install it with pip:

```bash
$ pip install django-proctor
```

Or add it to your `requirements.txt` file (preferably with the current version).

### Middleware

django-proctor does most of its processing in a middleware. This runs before your views and adds `proc` to the `request` object, which lets you access test group assignments.

You must subclass `proctor.middleware.BaseProctorMiddleware` and override several functions to provide django-proctor with information it needs to handle group assignments.

```py
class MyProctorMiddleware(proctor.middleware.BaseProctorMiddleware):
    ...
```

#### get_identifiers()

Identifiers are strings that identify users of your site uniquely. These can include tracking cookies and account ids. Proctor uses this information to keep users in the same test groups across requests.

This returns a dict of identifier source keys (see Pipet service configuration) to their values.

If a user lacks a certain identifier, don't include it in the dict. Proctor will skip any tests using that identifier. However, make sure you always return at least one identifier like a tracking cookie.

You **must** override this method.

This method is always run after any previous middleware.

```py
def get_identifiers(self, request):
    ids = {'USER': request.COOKIES.get('tracking')}

    if request.user.is_authenticated():
        ids['acctid'] = request.user.id

    return ids
```

#### get_context()

Context variables are properties about the user that are used in Proctor test rules to selectively enable tests or change the allocations of a test depending on whether an expression is true. This can be used to run a test only on Firefox, or you can run a test at 50% for US users and 10% for everyone else.

This returns a dict of context variable source keys (see Pipet service configuration) to their values, which are converted by Pipet to their final types before rule expressions are evaluated.

If you don't override this method, django-proctor uses no context variables.

If the Pipet service configuration doesn't have a default value for a context variable, it must be included on every API request. If that is the case, make sure that context variable appears in this return value.

This method is always run after any previous middleware.

```py
def get_context(self, request):
    return {"ua": request.META.get('HTTP_USER_AGENT', ''),
            "loggedIn": request.user.is_authenticated(),
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

### settings.py

You must set several things in your `settings.py` for django-proctor to work properly:

#### MIDDLEWARE_CLASSES

Add the middleware you created to `MIDDLEWARE_CLASSES`. Make sure you place it after any middleware it depends on like `AuthenticationMiddleware`.

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

TODO: intro, can be used in other frameworks, required config options,
basic usage, etc.
