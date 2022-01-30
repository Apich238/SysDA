from .estimates import *


def reduce(liters, name):
    company = [x for x in liters if x.expr.name == name]
    oth = [x for x in liters if x.expr.name != name]

    gsigns = ['>', '>=']
    lsigns = ['<', '<=']

    greaters = [x for x in company if x.cmpsign in gsigns]
    lessers = [x for x in company if x.cmpsign in lsigns]

    resg = None
    resl = None

    if len(greaters) > 1:  # φ ≥ a, φ ≥ b    ====>   φ ≥ max{a, b}
        m = 0
        for k, l in enumerate(greaters):
            if l.est > greaters[m].est:
                m = k
        cands = [x for x in greaters if x.est == greaters[m].est]
        if len(cands) == 1:
            resg = cands[0]
        else:
            s1 = [x for x in cands if x.cmpsign == '>']
            s2 = [x for x in cands if x.cmpsign == '>=']
            if len(s1) > 0:
                resg = s1[0]
            else:
                resg = s2[0]
    elif len(greaters) == 1:
        resg = greaters[0]

    if len(lessers) > 1:  # φ ≤ a, φ ≤ b      ====>        φ ≤ min{a, b
        m = 0
        for k, l in enumerate(lessers):
            if l.est < lessers[m].est:
                m = k
        cands = [x for x in lessers if x.est == lessers[m].est]
        if len(cands) == 1:
            resl = cands[0]
        else:
            s1 = [x for x in cands if x.cmpsign == '<']
            s2 = [x for x in cands if x.cmpsign == '<=']
            if len(s1) > 0:
                resl = s1[0]
            else:
                resl = s2[0]
    elif len(lessers) == 1:
        resl = lessers[0]

    if resg is not None and resl is not None:
        b = resg.cmpsign
        c = resl.cmpsign
        if resg.est > resl.est or resg.est == resl.est and (b, c) in [('>=', '<'), ('>', '<='), ('>', '<')]:
            return None

    if resg is not None:
        oth.append(resg)
    if resl is not None:
        oth.append(resl)

    return oth


def consistent_insert(liters, newlitera):
    names = set([x.expr.name for x in liters])
    if newlitera.expr.name not in names:
        return liters + [newlitera]
    else:
        new_liters = liters + [newlitera]
        res = reduce(new_liters, newlitera.expr.name)
        return res


def atables_open_branches(formulas, liters=None):
    if liters is None:
        liters = []

    # region defs
    def is_atom(f: Form):
        return isinstance(f, AtomForm) or isinstance(f, EstForm) and isinstance(f.expr, AtomForm)

    def is_alpha1(f: Form):
        '''
        истинно для формулы, елси при применении к ней правил, ко множеству термов прибавляется одно новое выражение
        :param f:
        :return:
        '''
        if isinstance(f, SignedForm):  # +- ~a
            if isinstance(f.expr, NegForm) or isinstance(f.expr, EstForm):
                return True
        elif isinstance(f, NegForm) and isinstance(f.value, EstForm):
            return True
        else:
            return isinstance(f, EstForm) and isinstance(f.expr, (AtomForm, NegForm))

    def is_alpha2(f: Form):
        '''
         истинно для формулы, если она - конъюнктивного типа, при разложении дающая нексколько термов
        :param f:
        :return:
        '''
        if isinstance(f, SignedForm):
            return f.positive and isinstance(f.expr, ConForm) or \
                   not f.positive and isinstance(f.expr, (DisForm, ImpForm))
        elif isinstance(f, EstForm):
            return isinstance(f.expr, ConForm) and f.cmpsign in ['>', '>='] or \
                   isinstance(f.expr, DisForm) and f.cmpsign in ['<', '<='] or \
                   isinstance(f.expr, ImpForm) and f.cmpsign in ['<', '<=']
        return isinstance(f, ConForm)

    def is_beta(f: Form):
        return not (is_alpha1(f) or is_alpha2(f))

    def select_formula(formulas: list):
        if len(formulas) == 0:
            return None

        for i, f in enumerate(formulas):
            if is_atom(f):
                return i
        for i, f in enumerate(formulas):
            if is_alpha1(f):
                return i
        for i, f in enumerate(formulas):
            if is_alpha2(f):
                return i
        for i, f in enumerate(formulas):
            if is_beta(f):
                return i
        return 0

    # endregion
    if len(formulas) == 0:
        return [liters]
    res = []
    locfs = formulas.copy()
    fi = select_formula(locfs)
    if fi is None:
        return []
    f = locfs[fi]
    locfs.pop(fi)
    # print('f:', f, 'forms:', locfs, 'lits:', liters)

    if is_atom(f):
        j = consistent_insert(liters, f)
        if j is not None:
            res.extend(atables_open_branches(locfs, j))
        else:
            return []

    elif is_alpha1(f):
        appendix = None
        if isinstance(f, SignedForm):
            if isinstance(f.expr, NegForm):  # +- ~a
                appendix = SignedForm(f.expr.value, '+' if not f.positive else '-')
            elif isinstance(f.expr, EstForm):  # +- a s r
                if f.positive:
                    d = {'>': '>',
                         '>=': '>=',
                         '<': '<',
                         '<=': '<='}
                else:
                    d = {'>=': '<',
                         '>': '<=',
                         '<=': '>',
                         '<': '>='
                         }
                appendix = EstForm(f.expr.expr, d[f.expr.cmpsign], f.expr.est)
        elif isinstance(f, NegForm):  # ~(a s r)
            assert isinstance(f.value, EstForm)
            s = f.value.cmpsign
            s1 = {'<': '>=', '<=': '>', '>': '<=', '>=': '<'}[s]
            # s1 = {'<=': '>=', '>=': '<='}[s]
            appendix = EstForm(f.value.expr, s1, f.value.est)
        elif isinstance(f, EstForm):  # (~a) s r
            assert isinstance(f.expr, NegForm)
            s = f.cmpsign
            # sinv = {'<': '>', '<=': '>=', '>': '<', '>=': '<='}
            s1 = {'<': '>',
                  '<=': '>=',
                  '>': '<',
                  '>=': '<='}[s]
            appendix = EstForm(f.expr.value, s1, round(1 - f.est, 6))
        res = atables_open_branches(locfs + [appendix], liters)

    elif is_alpha2(f):
        a = []
        if isinstance(f, EstForm):
            s = f.cmpsign
            r = f.est
            if isinstance(f.expr, ConForm):  # a&b > >= r
                a = [EstForm(sf, s, r) for sf in f.expr.members]
            elif isinstance(f.expr, DisForm):  # a|b < <= r
                a = [EstForm(sf, s, r) for sf in f.expr.members]
            elif isinstance(f.expr, ImpForm):  # a=>b < <= r
                a = [EstForm(f.expr.a, {'<': '>',
                                        '<=': '>='}[s], round(1 - r, 6)),
                     EstForm(f.expr.b, s, r)]
        elif isinstance(f, SignedForm):
            if isinstance(f.expr, ConForm):  # +a&b
                a = [SignedForm(sf, '+') for sf in f.expr.members]
            elif isinstance(f.expr, DisForm):  # -a|b
                a = [SignedForm(sf, '-') for sf in f.expr.members]
            elif isinstance(f.expr, ImpForm):  # -a=>b
                a = [SignedForm(f.expr.a, '+'),
                     SignedForm(f.expr.b, '-')]
        elif isinstance(f, ConForm):  # a&b&c
            a = f.members
        res = atables_open_branches(locfs + a, liters)
    else:  # beta
        alts = []

        if isinstance(f, EstForm):
            s = f.cmpsign
            r = f.est
            if isinstance(f.expr, ConForm):  # a&b < <= r
                alts = [EstForm(sf, s, r) for sf in f.expr.members]
            elif isinstance(f.expr, DisForm):  # a|b > >= r
                alts = [EstForm(sf, s, r) for sf in f.expr.members]
            elif isinstance(f.expr, ImpForm):  # a=>b > >= r
                alts = [EstForm(f.expr.a, '<=',  # {'>': '<', '>=': '<='}[s],
                                round(1 - r, 6)),
                        EstForm(f.expr.b, s, r)]
        elif isinstance(f, SignedForm):
            if isinstance(f.expr, ConForm):  # -a&b
                alts = [SignedForm(sf, '-') for sf in f.expr.members]
            elif isinstance(f.expr, DisForm):  # +a|b
                alts = [SignedForm(sf, '+') for sf in f.expr.members]
            elif isinstance(f.expr, ImpForm):  # +a=>b
                alts = [SignedForm(f.expr.a, '-'),
                        SignedForm(f.expr.b, '+')]

        elif isinstance(f, DisForm):
            alts = f.members
        for m in alts:
            res.extend(atables_open_branches([m] + locfs, liters))

    #     elif type(f) is AtomForm:
    #     j = consistent_insert(liters, f)
    #     if not j is None:
    #         res.extend(atables_open_branches(locfs, j))
    #     else:
    #         return []
    #
    # elif type(f) is DisForm:
    # for m in f.members:
    #     res.extend(atables_open_branches([m] + locfs, liters))
    # elif type(f) is NegForm:
    # sf = f.reduce()
    # if type(sf) is AtomForm or type(sf) is NegForm and type(sf.value) is AtomForm:
    #     j = consistent_insert(liters, sf)
    #     if not j is None:
    #         res.extend(atables_open_branches(locfs, j))
    #     else:
    #         return []
    # else:
    #     return atables_open_branches([sf] + locfs, liters)
    # else:
    # return []
    # # print('res:', res)
    return res


def litera_not_cover(branches, litera):
    res = []
    for l in branches:
        r = consistent_insert(l, litera)
        if r is None:
            res.append(l)
    return res


def filter(branches, liters):
    res = branches.copy()
    for l in liters:
        res = litera_not_cover(res, l)
        if len(res) == 0:
            break
    return res


# переборный метод преобразования бз
def KB2DNF(rs: list):
    # print('rs={}'.format(rs))
    if len(rs) == 0:
        return []
    elif len(rs) == 1:
        if type(rs[0]) is DisForm:
            return [consistent_insert([], a) for a in rs[0].members]
        else:
            return [[rs[0]]]
    res = []
    a = rs[0]
    rst = KB2DNF(rs[1:])
    # print('deb a={} rst={}'.format(a, rst))
    if type(a) is DisForm:
        variants = a.members
    else:
        variants = [a]
    for v in variants:
        sv = v.reduce()
        for r in rst:
            c = consistent_insert(r, sv)
            if not c is None:
                res.append(c)
    return res


def build_graph(P, C, Q):
    '''
    построение графа покрытий
    :param P:
    :param C:
    :param Q:
    :return:
    '''
    cs = {i: c for i, c in enumerate(C)}
    ps = {a: {} for a in P}
    qs = {a: {} for a in Q}
    for i, br in enumerate(C):
        for p in P:
            for est in br:
                if est.expr.name == p[0].name and est.cmpsign != p[1]:
                    ps[p][i] = round(1 - est.est, 6)
                    break
        for q in Q:
            for est in br:
                if est.expr.name == q[0].name and est.cmpsign != q[1]:
                    qs[q][i] = round(1 - est.est, 6)
                    break

    return cs, ps, qs


def simplify(kb: list):
    # def is_strong_subset(a, b):
    #     '''
    #     a - строгое подмножество b
    #     все элементы a содержатся в b, и длина a меньше чем у b
    #     :param a:
    #     :param b:
    #     :return:
    #     '''
    #     f = True
    #     for ae in a:
    #         f = ae in b
    #         if not f: break
    #     return f and len(a) < len(b)
    #
    # def minimal(f, kb):
    #     '''
    #
    #     :param f:
    #     :param kb:
    #     :return:
    #     '''
    #     fl = True
    #     for f2 in kb:
    #         fl = not (is_strong_subset(f2, f))
    #         if not fl: break
    #     return fl
    #
    # res = []
    # # kb = kb.copy()
    # # while len(kb) > 0:
    # #     cand = kb.pop(0)
    # #     if minimal(cand, kb):
    # #         res.append(cand)
    # for cand in kb:
    #     sc = sorted(cand, key=lambda x: str(x))
    #     if minimal(sc, kb) and not sc in res:
    #         res.append(sc)
    res=[list(y) for y in sorted(list({tuple(sorted(x,key=str)) for x in kb}),key=str)]
    return res


def abduce_by_graph(graph, negobs, Abd):
    C, G1, G2 = graph
    tC = C.copy()
    for p in negobs:
        print(p)
        psimplified = atables_open_branches([p])[0][0]
        print(psimplified)
        for i in tC:
            print('\t', tC[i], '\t')

        # tC = {i: C[i] for i in tC if not i in G1[p]}
        tC1 = {}
        pname = psimplified.expr.name
        psign = psimplified.cmpsign

        tC = tC1

        print()

        for i in tC:
            print('\t', tC[i], '\t')

    # print('Формулы БЗ, не покрытые наблюдением:')
    # for i in tC: print('\t',i, tC[i])

    cands = []
    for i in tC:
        for q in Abd:
            if NegForm(q).reduce() in tC[i]:
                cands.append(NegForm(q).reduce())
    cands = list(set(cands))
    # print(cands)

    res = []

    def reccover(uncovered: dict, candidats: list):
        if len(uncovered) == 0:
            return []
        if len(candidats) == 0:
            return None
        res = []
        for i in range(len(candidats)):
            c = candidats.copy()
            h = c.pop(i)
            # print('h,c ',h,c)
            new_uncovered = {k: uncovered[k] for k in uncovered if not h in uncovered[k]}
            # print('uncov',new_uncovered)
            if len(new_uncovered) == 0:
                res.append([h])
            else:
                res.extend([[h] + l for l in reccover(new_uncovered, c)])
        return res

    res = reccover(tC, cands)
    print('res', res)
    minres = simplify(res)
    print('minres', minres)

    # cands=[x for x in Abd if ]
    # hyps = []
    # print('Гипотезы:', hyps)
    # cw = {a: [x for x in skb2simp if not [NegForm(a).reduce(), x] in graph] for a in observation}
    # for a in cw: print('\t', a, cw[a])
    # for a in cw:
    #     l = cw[a]
    #     best = []
    #     candidats = abd.copy()
    #     score = len(l)  # сколько осталось покрыть
    #     print('a,l:', a, l)
    #     while score > 0:
    #         bestcand = None
    #         bestcandscore = score
    #         for c in candidats:
    #             newscore = len([x for x in l if NegForm(c).reduce() in x])
    #             if newscore < bestcandscore:
    #                 bestcand = c
    #                 bestcandscore = newscore
    #                 print('cand upd', c, bestcandscore)
    #         best.append(bestcand)
    #         score = bestcandscore
    #         l = [x for x in l if NegForm(bestcand).reduce() in x]
    #         print(score, best, l)
    return minres

