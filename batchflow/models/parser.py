""" Contains node-class of a syntax tree, builder of mathematical tokens (`sin`, `cos` and others)
and tree-parser.
"""

import numpy as np
import tensorflow as tf


def add_binary_magic(cls, operators=('__add__', '__radd__', '__mul__', '__rmul__', '__sub__', '__rsub__',
                                     '__truediv__', '__rtruediv__', '__pow__', '__rpow__')):
    """ Add binary-magic operators to `SyntaxTreeNode`-class.
    """
    for magic_name in operators:
        def magic(self, other, magic_name=magic_name):
            return cls(lambda x, y: getattr(x, magic_name)(y), self, other, name=magic_name)

        setattr(cls, magic_name, magic)
    return cls

@add_binary_magic
class SyntaxTreeNode():
    """ Node of parse tree. Stores operation along with its arguments.
    """
    def __init__(self, *args, name=None):
        arg = args[0]
        if isinstance(arg, str):
            if len(arg) == 1:
                nums_of_args = {'u': 0, 'x': 1, 'y': 2, 'z': 3, 't': -1}
                self.method = lambda *args: args[nums_of_args[arg]]
            else:
                self.method = lambda *args: args[int(arg[1])]
            self.name = arg
        elif callable(arg):
            self.method = arg
            self.name = name
        else:
            raise ValueError("Cannot create a NodeTree-instance")
        self._args = args[1:]

    def __len__(self):
        return len(self._args)

    def __repr__(self):
        return tuple((self.name, *self._args)).__repr__()

def parse(tree):
    """ Build the method represented by a parse-tree.
    """
    if isinstance(tree, (int, float)):
        # constants
        return lambda *args: tree
    else:
        def result(*args):
            if len(tree) > 0:
                all_args = [parse(operand)(*args) for operand in tree._args]
                return tree.method(*all_args)
            else:
                return tree.method(*args)
        return result

def make_tokens(module='tf', names=('sin', 'cos', 'exp', 'log', 'tan', 'acos', 'asin', 'atan',
                                    'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh', 'D'),
                namespaces=None, D_func=None):
    """ Make a collection of mathematical tokens.
    """
    # parse namespaces-arg
    if module in ['tensorflow', 'tf']:
        namespaces = namespaces if namespaces is not None else [tf.math, tf, tf.nn]
        D_func = lambda f, x: tf.gradients(f, x)[0]
    elif module == 'torch':
        pass
    elif module in ['numpy', 'np']:
        namespaces = namespaces if namespaces is not None else [np, np.math]
        if 'D' in names:
            import autograd.numpy as autonp
            namespaces = namespaces if namespaces is not None else [autonp, autonp.math]
            from autograd import grad
            D_func = lambda f, x: grad(f)(x)
    else:
        if namespaces is None:
            raise ValueError('Module ' + module + ' is not supported: you should directly pass namespaces-arg!')

    def _fetch_method(name, modules):
        for module in modules:
            try:
                return getattr(module, name)
            except:
                pass
        raise ValueError('Cannot find method ' + name + ' in ' + [str(module) for module in modules].join(', '))

    # fill up tokens-list
    tokens = []
    for name in names:
        # make the token-method
        method = D_func if name == 'D' else _fetch_method(name, namespaces)

        # make the token
        token = lambda *args, method=method, name=name: SyntaxTreeNode(method, *args, name=name)
        tokens.append(token)

    return tokens
