from reprlib import recursive_repr
import inspect


class ReprMixin(object):
    """This mixin gives a reasonably smart automatic __repr__.
    
    It hasn't been extensively tested - might fail, so test yourself!"""

    @recursive_repr()
    def __repr__(self):
        sig = inspect.signature(self.__init__)
        # NOTE: str(sig) gives the raw signature, but without self
        used_keys = []
        s_args = []
        for k, param in sig.parameters.items():
            if param.kind == inspect._VAR_KEYWORD:
                # 'kwargs'
                dct = getattr(self, "__dict__", {})
                for k, v in dct.items():
                    if k not in used_keys:
                        try:
                            val = getattr(self, k)
                            s_args.append(f"{k}={repr(val)}")
                        except AttributeError:
                            s_args.append(f"{k}=<?>")
                        used_keys.append(k)
            elif param.kind in [inspect._KEYWORD_ONLY, inspect._POSITIONAL_OR_KEYWORD]:
                # keyword-able
                try:
                    val = getattr(self, k)
                    if val != param.default:  # could be 'empty'
                        s_args.append(f"{k}={repr(val)}")
                except AttributeError:
                    s_args.append(f"{k}=<?>")
                used_keys.append(k)
        res = f"{self.__class__.__name__}("
        res += ", ".join(s_args) + ")"
        return res


if __name__ == "__main__":

    class Z(ReprMixin):
        def __init__(self, a, b=1, *, c: int = 8, **kwargs):
            self.a = a
            self.b = b
            self.c = c
            for k, v in kwargs.items():
                setattr(self, k, v)

    repr(Z(3))
    repr(Z(1, c=3, q=4))
    repr(Z(1, 2, c=3, other=Z(3, 2)))
    q = Z(1, 2)
    q.other = q
    repr(q)
