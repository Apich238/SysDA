from .myPEG import *


class Form:

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return self.__repr__().__hash__()

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

    def subst(self, subst_dict):
        pass


class AtomForm(Form):
    def __init__(self, name):
        super(Form, self).__init__()
        self.name = name

    def __repr__(self, br=False):
        return self.name

    def subst(self, subst_dict):
        return self


class RuleDummyForm(Form):
    def __init__(self, name):
        super(Form, self).__init__()
        self.name = name

    def __repr__(self, br=False):
        return self.name

    def subst(self, subst_dict):
        if self.name in subst_dict:
            return subst_dict[self.name]
        else:
            return self


class NegForm(Form):
    def __init__(self, value):
        super(Form, self).__init__()
        self.value = value

    def __repr__(self, br=False):
        return ('~{}' if isinstance(self.value, (AtomForm, NegForm)) else '~({})').format(self.value)

    def subst(self, subst_dict):
        return NegForm(self.value.subst(subst_dict))


class SetForm(Form):
    def __init__(self, members=None):
        super().__init__()
        if members is None:
            self.members = []
        else:
            self.members = members.copy()

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        a = self.members.copy()
        a = sorted(a, key=str)
        b = other.members.copy()
        b = sorted(b, key=str)
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if x != y:
                return False
        return True


class ConForm(SetForm):
    def __init__(self, members):
        super().__init__(members)

    def __repr__(self, br=False):
        return '1' if len(self.members) == 0 else ('({})' if br else '{}').format(
            '&'.join([a.__repr__(br=(isinstance(a, DisForm))) for a in self.members]))

    def subst(self, subst_dict):
        return ConForm(members=[x.subst(subst_dict) for x in self.members])


class DisForm(SetForm):
    def __init__(self, members):
        super().__init__(members)

    def __repr__(self, br=False):
        return '0' if len(self.members) == 0 else ('({})' if br else '{}').format(
            '|'.join([str(a) for a in self.members]))

    def subst(self, subst_dict):
        return DisForm(members=[x.subst(subst_dict) for x in self.members])


class ImpForm(Form):
    def __init__(self, a: Form, b: Form):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self, br=False):
        sa = ('({})' if isinstance(self.a, (ImpForm, EstForm)) else '{}').format(self.a)
        sb = ('({})' if isinstance(self.b, (ImpForm, EstForm)) else '{}').format(self.b)
        return sa + '=>' + sb

    def subst(self, subst_dict):
        return ImpForm(self.a.subst(subst_dict), self.b.subst(subst_dict))


def eval_expr(expr):
    if isinstance(expr, list):
        if expr[1] == '-':
            return expr[0] - expr[2]
        elif expr[0] == 'max':
            return max(expr[1], expr[2])
        elif expr[0] == 'min':
            return min(expr[1], expr[2])
        else:
            raise ValueError()
    else:
        raise ValueError()


class EstForm(Form):
    def __init__(self, expr: Form, cmpsign, est: float):
        # TODO: использовать decimal
        self.expr = expr
        if cmpsign in ['<=', '<', '>', '>=']:
            self.cmpsign = cmpsign
        else:
            raise ValueError()
        if (isinstance(est, float) and est >= 0 and est <= 1) or (isinstance(est, (RuleDummyForm, list))):
            self.est = est
        else:
            raise ValueError()

    def subst(self, subst_dict):
        ee = self.expr.subst(subst_dict)
        if (isinstance(self.est, float)):
            return EstForm(ee, self.cmpsign, self.est)
        elif (isinstance(self.est, RuleDummyForm)):
            return EstForm(ee, self.cmpsign, self.est.subst(subst_dict))
        elif (isinstance(self.est, list)):
            return EstForm(ee, self.cmpsign,
                           eval_expr([(x if not isinstance(x, Form) else x.subst(subst_dict)) for x in self.est]))

    def __repr__(self, br=False):
        return '{}{}{}'.format(str(self.expr), self.cmpsign, self.est)


class SignedForm(Form):
    def __init__(self, expr, sign=None, positive=True):
        if sign is not None and sign in ['-', '+']:
            self.positive = sign == '+'
        else:
            self.positive = positive
        self.expr = expr

    def __repr__(self, br=False):
        return '{}{}'.format('+' if self.positive else '-', self.expr)

    def subst(self, subst_dict):
        return SignedForm(self.expr.subst(subst_dict), None, self.positive)


def make_estimates_parser():
    # return PEG('start',
    #            {
    #                'atom': '[a-z][0-9a-z]*',
    #                'rule_dummy': '[A-Z]+',
    #                'estval': r'1|0(\.[0-9]*)?',
    #                'ops': '[(]',
    #                'cls': '[)]',
    #                'neg': '~',
    #                'disj': r'\|',
    #                'conj': r'&',
    #                'impl': r'=>',
    #                'sign': r'\+|-',
    #                'cmpsign': '<=|>=|<|>'
    #            },
    #            {
    #                'prop': sel('propimp', 'propdis'),
    #                'propimp': ['propdis', 'impl', 'propdis'],
    #                'propdis': ['propcon', zom(['disj', 'propcon'])],
    #                'propcon': ['atomicprop', zom(['conj', 'atomicprop'])],
    #                'atomicprop': sel('atom', 'rule_dummy', ['neg', 'atomicprop'], ['ops', 'prop', 'cls']),
    #                'estprop': ['prop', 'cmpsign', sel('estval', 'rule_dummy')],
    #                'estlog': sel('estimp', 'estdis'),
    #                'estimp': ['estdis', 'impl', 'estdis'],
    #                'estdis': ['estcon', zom(['disj', 'estcon'])],
    #                'estcon': ['estatomic', zom(['conj', 'estatomic'])],
    #                'estatomic': sel('estprop', ['neg', 'estatomic'], ['ops', 'estlog', 'cls']),
    #                'start': [opt('sign'), 'estlog']
    #            }
    #            )
    return PEG('start',
               {
                   'atom': '[abcdpqwxyz][0-9a-z]*',
                   'rule_dummy': '[A-Z]+',
                   'number': r'1|0(\.[0-9]*)?',
                   'min': 'min',
                   'max': 'max',
                   'comma': ',',
                   'ops': '[(]',
                   'cls': '[)]',
                   'neg': '~',
                   'disj': r'\|',
                   'conj': r'&',
                   'impl': r'=>',
                   'sign': r'\+|-',
                   'cmpsign': '<=|>=|<|>'
               },
               {
                   'mathexpr': sel([sel('min', 'max'), 'ops', 'arithmvalue', 'comma', 'arithmvalue', 'cls'],
                                   ['number', 'sign', 'arithmvalue']),
                   'arithmvalue': sel('mathexpr', 'number', 'rule_dummy'),

                   'proplog': sel('propimp', 'propdis'),
                   'propimp': ['propdis', 'impl', 'propdis'],
                   'propdis': ['propcon', zom(['disj', 'propcon'])],
                   'propcon': ['atomicprop', zom(['conj', 'atomicprop'])],
                   'atomicprop': sel('atom', 'rule_dummy', ['neg', 'atomicprop'], ['ops', 'proplog', 'cls']),

                   'estlog': sel('estimp', 'estdis'),
                   'estprop': ['proplog', 'cmpsign', 'arithmvalue'],
                   'estimp': ['estdis', 'impl', 'estdis'],
                   'estdis': ['estcon', zom(['disj', 'estcon'])],
                   'estcon': ['estatomic', zom(['conj', 'estatomic'])],
                   'estatomic': sel('estprop', 'proplog', ['neg', 'estatomic'], ['ops', 'estlog', 'cls']),

                   'start': [opt('sign'), 'estlog']
               }
               )


def syn2ast(node: TNode):
    if len(node.childs) == 2 and node.childs[1].symbol == 'zom':
        sym = 'con' if node.symbol in ['propcon', 'estcon'] else 'dis'
        res = TNode(sym)
        res.add(syn2ast(node.childs[0]))
        for sq in node.childs[1].childs:
            if sq.symbol == 'seq':
                # for c in sq.childs:
                #     res.add(syn2ast(c))
                res.add(syn2ast(sq.childs[1]))
        return res
    elif node.symbol == 'seq' and len(node.childs) == 2 and \
            isinstance(node.childs[0].symbol, Token) and \
            node.childs[0].symbol.type == 'neg':

        res = TNode(node.childs[0].symbol)
        res.add(syn2ast(node.childs[1]))
        return res
    elif node.symbol == 'seq' and len(node.childs) == 3 and \
            isinstance(node.childs[0].symbol, Token) and \
            node.childs[0].symbol.type == 'ops':
        return syn2ast(node.childs[1])
    elif node.symbol in ['propimp', 'estimp']:
        a = syn2ast(node.childs[0])
        b = syn2ast(node.childs[2])
        res = TNode('imp')
        res.add(a)
        res.add(b)
        return res
    elif node.symbol == 'estprop':
        res = TNode(node.childs[1].symbol)
        res.add(syn2ast(node.childs[0]))
        res.add(node.childs[2])
        return res
    elif len(node.childs) > 0 and \
            isinstance(node.childs[0].symbol, Token) and \
            node.childs[0].symbol.type == 'sign':
        res = TNode(node.childs[0].symbol)
        for c in node.childs[1:]:
            res.add(syn2ast(c))
        return res
    elif len(node.childs) == 1:
        return syn2ast(node.childs[0])
    else:
        res = TNode(node.symbol)
        for c in node.childs:
            res.add(syn2ast(c))
        return res


def compile_ast(node):
    if isinstance(node.symbol, Token) and node.symbol.type == 'sign':
        return SignedForm(compile_ast(node.childs[0]), node.symbol.value)
    elif isinstance(node.symbol, Token) and node.symbol.type == 'cmpsign':
        if isinstance(node.childs[1].symbol, Token) and node.childs[1].symbol.type == 'rule_dummy':
            return EstForm(
                compile_ast(node.childs[0]),
                node.symbol.value,
                RuleDummyForm(node.childs[1].symbol.value))
        elif isinstance(node.childs[1].symbol, str) and node.childs[1].symbol == 'seq':
            # arithmetic formula as estimate
            fl = []
            for ch in node.childs[1].childs:
                if ch.symbol.type == 'number':
                    fl.append(float(ch.symbol.value))
                elif ch.symbol.type == 'sign':
                    fl.append(ch.symbol.value)
                elif ch.symbol.type == 'rule_dummy':
                    fl.append(RuleDummyForm(ch.symbol.value))
                elif ch.symbol.type == 'min':
                    fl.append(ch.symbol.value)
                elif ch.symbol.type == 'max':
                    fl.append(ch.symbol.value)
                elif ch.symbol.type == 'ops':
                    continue
                elif ch.symbol.type == 'cls':
                    continue
                elif ch.symbol.type == 'comma':
                    continue
                else:
                    raise NotImplementedError(' ')
            return EstForm(
                compile_ast(node.childs[0]),
                node.symbol.value,
                fl)
        else:
            return EstForm(
                compile_ast(node.childs[0]),
                node.symbol.value,
                float(node.childs[1].symbol.value))
    elif isinstance(node.symbol, Token) and node.symbol.type == 'atom':
        return AtomForm(node.symbol.value)
    elif isinstance(node.symbol, Token) and node.symbol.type == 'rule_dummy':
        return RuleDummyForm(node.symbol.value)
    elif node.symbol == 'imp':
        return ImpForm(compile_ast(node.childs[0]), compile_ast(node.childs[1]))
    elif node.symbol == 'con':
        return ConForm([compile_ast(c) for c in node.childs])
    elif node.symbol == 'dis':
        return DisForm([compile_ast(c) for c in node.childs])
    elif isinstance(node.symbol, Token) and node.symbol.type == 'neg':
        return NegForm(compile_ast(node.childs[0]))
    return ConForm([])


def parse_formula(p: PEG, l: str) -> Form:
    syntree = p.Parse(l)
    ast = syn2ast(syntree)
    res = compile_ast(ast)
    return res
