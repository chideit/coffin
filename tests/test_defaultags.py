﻿from jinja2 import Environment


def test_load():
    from coffin.template.defaulttags import LoadExtension
    env = Environment(extensions=[LoadExtension])

    # the load tag is a no-op
    assert env.from_string('a{% load %}b').render() == 'ab'
    assert env.from_string('a{% load news.photos %}b').render() == 'ab'
    assert env.from_string('a{% load "news.photos" %}b').render() == 'ab'

    # [bug] invalid code was generated under certain circumstances
    assert env.from_string('{% set x=1 %}{% load "news.photos" %}').render() == ''


def test_url():
    from coffin.template.defaulttags import URLExtension
    from jinja2.exceptions import TemplateSyntaxError
    from django.core.urlresolvers import NoReverseMatch
    env = Environment(extensions=[URLExtension])

    for template, context, expected_result in (
        # various ways to specify the view
        ('{% url urls_app.views.index %}', {}, '/url_test/'),
        ('{% url apps.urls_app.views.index %}', {}, '/url_test/'),  # project name is optional
        ('{% url "urls_app.views.index" %}', {}, '/url_test/'),
        ('{% url "urls_app.views.indexXX"[:-2] %}', {}, '/url_test/'),
        ('{% url the-index-view %}', {}, '/url_test/'),

        # various ways to specify the arguments
        ('{% url urls_app.views.sum 1,2 %}', {}, '/url_test/sum/1,2'),
        ('{% url urls_app.views.sum left=1,right=2 %}', {}, '/url_test/sum/1,2'),
        ('{% url urls_app.views.sum l,2 %}', {'l':1}, '/url_test/sum/1,2'),
        ('{% url urls_app.views.sum left=l,right=2 %}', {'l':1}, '/url_test/sum/1,2'),
        ('{% url urls_app.views.sum left=2*3,right=z()|length %}',
                {'z':lambda: 'u'}, '/url_test/sum/6,1'),   # full expressive syntax

        # failures
        ('{% url %}', {}, TemplateSyntaxError),
        ('{% url 1,2,3 %}', {}, TemplateSyntaxError),
        ('{% url inexistant-view %}', {}, NoReverseMatch),

        # ValueError, not TemplateSyntaxError:
        # We actually support parsing a mixture of positional and keyword
        # arguments, but reverse() doesn't handle them.
        ('{% url urls_app.views.sum left=1,2 %}', {'l':1}, ValueError),

        # as-syntax
        ('{% url urls_app.views.index as url %}', {}, ''),
        ('{% url urls_app.views.index as url %}{{url}}', {}, '/url_test/'),
        ('{% url inexistent as url %}{{ url }}', {}, ''),    # no exception
    ):
        try:
            actual_result = env.from_string(template).render(context)
        except Exception, e:
            assert type(e) == expected_result
        else:
            assert actual_result == expected_result


def test_with():
    from coffin.template.defaulttags import WithExtension
    env = Environment(extensions=[WithExtension])

    assert env.from_string('{{ x }}{% with y as x %}{{ x }}{% endwith %}{{ x }}').render({'x': 'x', 'y': 'y'}) == 'xyx'


def test_cache():
    from coffin.template.defaulttags import CacheExtension
    env = Environment(extensions=[CacheExtension])

    x = 0
    assert env.from_string('{%cache 500 "ab"%}{{x}}{%endcache%}').render({'x': x}) == '0'
    # cache is used; Jinja2 expressions work
    x += 1
    assert env.from_string('{%cache 50*10 "a"+"b"%}{{x}}{%endcache%}').render({'x': x}) == '0'
    # vary-arguments can be used
    x += 1
    assert env.from_string('{%cache 50*10 "ab" x "foo"%}{{x}}{%endcache%}').render({'x': x}) == '2'
    x += 1
    assert env.from_string('{%cache 50*10 "ab" x "foo"%}{{x}}{%endcache%}').render({'x': x}) == '3'
