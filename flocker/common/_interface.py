# Copyright ClusterHQ Inc.  See LICENSE file for details.

"""
Some interface-related tools.
"""

from inspect import getargspec
from characteristic import attributes, Attribute
from zope.interface.interface import Method


def interface_decorator(decorator_name, interface, method_decorator,
                        *args, **kwargs):
    """
    Create a class decorator which applies a method decorator to each method of
    an interface.

    Sample Usage::
        class IDummy(Interface):
            def return_method():
                pass

        @implementer(IDummy)
        class Dummy():
            def return_method(self):
                pass

        def method_decorator(method_name, original_name):
            def _run_with_logging(self):
                Log()
            return _run_with_logging

        logged_dummy = interface_decorator("decorator", IDummy,
                                           method_decorator, _dummy=Dummy())

    :param str decorator_name: A human-meaningful name for the class decorator
        that will be returned by this function.
    :param zope.interface.InterfaceClass interface: The interface from which to
        take methods.
    :param method_decorator: A callable which will decorate a method from the
        interface.  It will be called with the name of the method as the first
        argument and any additional positional and keyword arguments passed to
        ``_interface_decorator``.

    :return: The class decorator.
    """
    for method_name in interface.names():
        if not isinstance(interface[method_name], Method):
            raise TypeError(
                "{} does not support interfaces with non-methods "
                "attributes".format(decorator_name)
            )

    def class_decorator(cls):
        for name in interface.names():
            setattr(cls, name, method_decorator(name, *args, **kwargs))
        return cls
    return class_decorator


def provides(interface):
    """
    Create an invariant that asserts that the given value provides the given
    interface.

    :param InterfaceClass interface: The interface to check for.

    :return: A function that takes an object and returns a tuple of `bool` and
        a error message.
    """
    interface_name = interface.__name__

    def invariant(value):
        if interface.providedBy(value):
            return (True, "")
        else:
            return (False, "{value!r} doesn't provide {interface}".format(
                value=value, interface=interface_name,
            ))
    invariant.__name__ = "provides_{}_invariant".format(interface_name)

    return invariant


@attributes([
    Attribute("unexpected_arguments", default_value=frozenset()),
    Attribute("missing_arguments", default_value=frozenset()),
    Attribute("missing_optional_arguments", default_value=frozenset())
])
class InvalidSignature(Exception):
    """
    See :func:`validate_signature_against_kwargs` raises clause.
    """
    def __str__(self):
        return repr(self)


def validate_signature_against_kwargs(function, keyword_arguments):
    """
    Validates that ``function`` can be called with keyword arguments with
    exactly the specified ``keyword_arguments_keys``. In this case validation
    is verifying that the function's signature allows it to be called with
    exactly the given keyword arguments.

    :param function: The function of which to verify the signature.
    :param set keyword_arguments_keys: A set of keyword argument names to
        validate against the function signature.

    :returns: ``None`` if the validation succeeds.

    :raises InvalidSignature: If validation fails.
    """
    arg_spec = getargspec(function)
    accepted_arguments = frozenset(arg_spec.args)
    optional_arguments = frozenset()
    if arg_spec.defaults is not None:
        optional_arguments = frozenset(arg_spec.args[-len(arg_spec.defaults):])

    unexpected_arguments = frozenset(keyword_arguments - accepted_arguments)
    missing_arguments = frozenset(
        accepted_arguments - keyword_arguments - optional_arguments)

    if missing_arguments != frozenset() or unexpected_arguments != frozenset():
        raise InvalidSignature(
            unexpected_arguments=unexpected_arguments,
            missing_arguments=missing_arguments,
            missing_optional_arguments=frozenset(
                optional_arguments - keyword_arguments)
        )
