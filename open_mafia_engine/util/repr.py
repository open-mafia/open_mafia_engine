import inspect
from reprlib import recursive_repr


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
        res = f"{self.__class__.__qualname__}(" + ", ".join(s_args) + ")"
        return res
