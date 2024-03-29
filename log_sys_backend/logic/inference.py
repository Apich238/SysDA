try:
    from .estimates import *
except ImportError as e:
    from estimates import *


def interpret_comparison(e: EstForm):
    if e.cmpsign == '<':
        return e.expr < e.est
    if e.cmpsign == '<=':
        return e.expr <= e.est
    if e.cmpsign == '>':
        return e.expr > e.est
    if e.cmpsign == '>=':
        return e.expr >= e.est
    raise TypeError()


class infrule:
    def __init__(self, format_in, format_out, priority, id):
        ep = make_estimates_parser()
        self.format_in = format_in
        self.id = id
        self.format_in_f = [parse_formula(ep, x) for x in format_in]

        self.format_in_f_additional = []  # условия на только оценки
        if len(self.format_in_f) > 2 and isinstance(self.format_in_f[-1], EstForm):
            uu = self.format_in_f.pop(-1)
            self.format_in_f_additional = [uu]

        self.format_out = format_out
        if format_out is not None:
            self.format_out_f = [[parse_formula(ep, pf) for pf in l] for l in format_out]
        else:
            self.format_out_f = None
        self.priority = priority

    def apply(self, dummies_matching_dict):
        if self.format_out_f is None:
            return None
        res = [[m.subst(dummies_matching_dict) for m in bs] for bs in self.format_out_f]
        return res

    def __str__(self):
        return '{} & {} |-> {}'.format(self.format_in_f, self.format_in_f_additional, self.format_out_f)


def try_to_match_one_formula(sf, pattern):
    # returns substitution if formula matches pattern, and None otherwise
    dummies_matching_dict = {}
    if isinstance(sf, atree):
        sf = sf.formula
    if isinstance(pattern, RuleDummyForm):
        return {pattern.name: sf}
    if not isinstance(sf, type(pattern)):
        return None
    # types are same. matching childs
    if isinstance(sf, (ConForm, DisForm)):
        if len(sf.members) != len(pattern.members):
            # match first elements and then second to last with second rule member
            t1 = try_to_match_one_formula(sf.members[0], pattern.members[0])
            if t1 is None:
                return None
            dummies_matching_dict.update(t1)
            fld = (ConForm if isinstance(sf, ConForm) else DisForm)(sf.members[1:])
            t2 = try_to_match_one_formula(fld, pattern.members[1])
            if t2 is None:
                return None
            dummies_matching_dict.update(t2)
        else:
            for i in range(len(sf.members)):
                t = try_to_match_one_formula(sf.members[i], pattern.members[i])
                if t is None:
                    return None
                dummies_matching_dict.update(t)
        return dummies_matching_dict

    elif isinstance(sf, NegForm):
        return try_to_match_one_formula(sf.value, pattern.value)
    elif isinstance(sf, ImpForm):
        t1 = try_to_match_one_formula(sf.a, pattern.a)
        if t1 is None:
            return None
        t2 = try_to_match_one_formula(sf.b, pattern.b)
        if t2 is None:
            return None
        dummies_matching_dict.update(t1)
        dummies_matching_dict.update(t2)
        return dummies_matching_dict
    elif isinstance(sf, EstForm):
        if sf.cmpsign != pattern.cmpsign:
            return None
        if isinstance(pattern.est, RuleDummyForm):
            dummies_matching_dict[pattern.est.name] = sf.est
        elif isinstance(pattern.est, float):
            if pattern.est != sf.est:
                return None
        else:
            raise TypeError()
        t = try_to_match_one_formula(sf.expr, pattern.expr)
        if t is None:
            return None
        dummies_matching_dict.update(t)
        return dummies_matching_dict
    else:
        raise ValueError()


"""
приоритеты:
1 - альфа-формулы
2 - бета-формулы
3 - сокращения литер
4 - замыкания
поля:
-идентификатор/имя
-шаблон
-результат
-приоритет
"""

rules_base = [
    # правила ветвления
    ['t1r01', ['~~A'], [['A']], 2],
    ['t1r02', ['(A&B)'], [['A', 'B']], 2],
    ['t1r02C', ['~(A&B)'], [['~A'], ['~B']], 1],
    ['t1r03', ['(A|B)'], [['A'], ['B']], 1],
    ['t1r03C', ['~(A|B)'], [['~A', '~B']], 2],
    ['t1r04', ['(A=>B)'], [['~A'], ['B']], 1],
    ['t1r04C', ['~(A=>B)'], [['A', '~B']], 2],

    ['t1r05', ['~(A>=X)'], [['A<X']], 2],
    ['t1r06', ['~(A>X)'], [['A<=X']], 2],
    ['t1r07', ['~(A<=X)'], [['A>X']], 2],
    ['t1r08', ['~(A<X)'], [['A>=X']], 2],

    ['t1r09', ['(~A)>=X'], [['A<=1-X']], 2],
    ['t1r10', ['(~A)>X'], [['A<1-X']], 2],
    ['t1r11', ['(~A)<=X'], [['A>=1-X']], 2],
    ['t1r12', ['(~A)<X'], [['A>1-X']], 2],

    ['t1r13', ['(A&B)>=X'], [['A>=X', 'B>=X']], 2],
    ['t1r14', ['(A&B)>X'], [['A>X', 'B>X']], 2],
    ['t1r15', ['(A&B)<=X'], [['A<=X'], ['B<=X']], 1],
    ['t1r16', ['(A&B)<X'], [['A<X'], ['B<X']], 1],

    ['t1r17', ['(A|B)>=X'], [['A>=X'], ['B>=X']], 1],
    ['t1r18', ['(A|B)>X'], [['A>X'], ['B>X']], 1],
    ['t1r19', ['(A|B)<=X'], [['A<=X', 'B<=X']], 2],
    ['t1r20', ['(A|B)<X'], [['A<X', 'B<X']], 2],

    ['t1r21', ['(A=>B)>=X'], [['A<=1-X'], ['B>=X']], 1],
    ['t1r22', ['(A=>B)>X'], [['A<1-X'], ['B>X']], 1],
    ['t1r23', ['(A=>B)<=X'], [['A>=1-X', 'B<=X']], 2],
    ['t1r24', ['(A=>B)<X'], [['A>1-X', 'B<X']], 2],

    # правила сокращения литер

    ['t2r07', ['A>=X', 'A>=Y'], [['A>=max(X,Y)']], 3],
    ['t2r08', ['A>=X', 'A>Y'], [['A>max(X,Y)']], 3],
    ['t2r09', ['A>=X', 'A>Y'], [['A>max(X,Y)']], 3],
    ['t2r10', ['A>X', 'A>Y'], [['A>max(X,Y)']], 3],

    ['t2r11', ['A<=X', 'A<=Y'], [['A<=min(X,Y)']], 3],
    ['t2r12', ['A<=X', 'A<Y'], [['A<min(X,Y)']], 3],
    ['t2r13', ['A<X', 'A<=Y'], [['A<min(X,Y)']], 3],
    ['t2r14', ['A<X', 'A<Y'], [['A<min(X,Y)']], 3],

    # правила выявления противоречий

    ['t1r25', ['A', '~A'], None, 4],

    ['t1r26', ['A>=X', 'A<X'], None, 4],
    ['t1r27', ['A>X', 'A<X'], None, 4],
    ['spec1', ['A>X', 'A<=X'], None, 4],

    ['t1r2829', ['A>=X', 'A<=Y', 'X>Y'], None, 4],
    ['t1r3031', ['A>X', 'A<=Y', 'X>=Y'], None, 4],
    ['t1r3233', ['A>X', 'A<Y', 'X>=Y'], None, 4],

]

rules = [infrule(x[1], x[2], x[3], x[0]) for x in rules_base]

rules = sorted(rules, key=lambda x: x.priority * 10 - 1 * len(x.format_in), reverse=True)


class counter:
    def __init__(self):
        self._i = 0

    def inc(self):
        a = self._i
        self._i += 1
        return a

    def get(self):
        return self._i

    def __repr__(self):
        return 'i={}'.format(self._i)


from itertools import product


class atree:
    def __init__(self, formulas=None, rule_id='init', cntr=None, step=None):
        if cntr is None:
            cntr = counter()
        self.cntr = cntr
        if step is None:
            self.step = cntr.get()
        else:
            self.step = step
        self.rule_id = rule_id
        self.usages = []
        if formulas is not None:
            self.formula = formulas[0]
        else:
            self.formula = None
        self.closed = False
        self.childs = []
        if isinstance(formulas, list) and len(formulas) > 1:
            self.childs.append(atree(formulas[1:], rule_id, cntr, step))

    def __repr__(self):
        if self.closed:
            return '(X)'
        elif self.formula is None:  # == 0:
            return '(O)'
        return '{}: {} {}'.format(self.step, str(self.formula), self.usages)

    def to_dict(self):
        if self.closed:
            return {'name': '{}(rule {}):(X)'.format(self.step, self.rule_id), 'children': []}
        elif len(self.childs) == 0:
            return {'name': '{}(rule {}):(O)'.format(self.step, self.rule_id), 'children': []}
        return {'name': '{}(rule {}):{}[{}]'.format(self.step, self.rule_id, self.formula, self.usages),
                'children': [x.to_dict() for x in self.childs]}

    def build(self, branch_prefix=None, used=None):
        if branch_prefix is None:
            branch_prefix = []
            used = []
        branch_prefix = branch_prefix + [self]

        # print(branch_prefix)

        used = used + [False]
        if len(self.childs) > 0:
            for ch in self.childs:
                ch.build(branch_prefix, used)
        elif not self.closed:
            # выбор правила и предпосылок
            # резальтат применения правила записывается в текущий узел и его потомки
            # правила уже отсортированы по приоритету
            # 1. сначала выбираем среди только неиспользованных формул
            used_mask = [0 if used[i] else 1 for i in range(len(branch_prefix))]
            t = self.select_action(branch_prefix, used_mask, rules)
            if t is not None:
                rule_i, matching_ids, subst_dict = t

            # 3. если и в этот раз не подобрали правило - ветвь открытая
            if t is None:
                self.cntr.inc()
                step = self.cntr.get()
                nt = atree(None, 'no_rule', self.cntr, step)
                self.childs = [nt]
            else:  # иначе:
                # применение правила
                rule = rules[rule_i]
                selected_nodes = [branch_prefix[k] for k in matching_ids]
                res = rule.apply(subst_dict)
                # пометка использованных формул
                self.cntr.inc()
                step = self.cntr.get()
                for nd in selected_nodes:
                    nd.usages.append(step)
                for ndi in matching_ids:
                    used[ndi] = True
                # добавление потомков
                self.childs = []
                if res is None:  # замкнутая ветвь

                    nt = atree(None)
                    nt.step = step
                    nt.formula = '(X)'
                    nt.rule_id = rule.id
                    nt.cntr = self.cntr
                    nt.closed = True
                    self.childs = [nt]
                    return
                for sub_branch in res:
                    nt = atree(sub_branch, rule.id, self.cntr, step)
                    self.childs.append(nt)
                # рекурсивный вызов
                for ch in self.childs:
                    ch.build(branch_prefix, used)

    def select_action(self, nodes, nodel_mask, rules):

        def generate_substitutions_rec(k, n_list):
            if k == 1:
                for x in n_list:
                    yield [x]
            else:
                for j, e in enumerate(n_list):
                    t = n_list[:j] + n_list[j + 1:]
                    for t in generate_substitutions_rec(k - 1, t):
                        yield [e] + t

        def join_substs(s1, s2):
            # объединяет 2 подстановки. если они не совместны - возвращает None
            s_joined = s1.copy()
            for k in s2:
                if k in s_joined and s1[k] != s2[k]:
                    return None
                else:
                    s_joined[k] = s2[k]
            return s_joined

        def check_rule(nodes, rule, nodes_mask):
            ########################
            # дано правило и список узлов.
            # надо определить, есть ли среди узлов такие, что формируют предпосылку для правила
            # если есть - вернуть индексы, соответственно порядку в правиле
            # если нет - вернуть None

            # берём индексы узлов по маске
            nodes_ids = [i for i in range(len(nodes)) if nodes_mask[i]]

            # v1
            # генерируем все подстановки узлов на место выражений в правиле
            # substitutions = generate_substitutions_rec(len(rule.format_in_f), nodes_ids)

            # for i, ids in enumerate(substitutions):
            #     selected = [nodes[j] for j in ids]
            #     x = rule.try_to_match(selected)
            #     if x is not None:
            #         return ids, x

            # v2
            # строим все возможные сопоставления всех правил и шаблонов, потом выбираем совместный набор сопоставлений
            matches = []
            for i, pattern in enumerate(rule.format_in_f):
                l = []
                for ni in nodes_ids:
                    simple_match = try_to_match_one_formula(nodes[ni], pattern)
                    if simple_match is not None:
                        l.append((ni, simple_match))
                matches.append(l)

            for t in product(*matches):
                # все сопоставления должны относиться к разным формулам. поэтому считаем количество различных индексов
                # в сопоставлении и если оно меньше числа шаблонов  в правиле - пропускаем
                if len({x[0] for x in t}) < len(t):
                    continue

                # надо проверить словари из списка на совместимость
                # будем составлять общий словарь-подстановку. если получится - подстановки применима.
                subst = {}
                fls = []
                for ni, pt_subst in t:
                    subst = join_substs(subst, pt_subst)
                    if subst is not None:
                        fls.append(ni)
                    else:
                        break
                if subst is not None:
                    if len(rule.format_in_f_additional) == 0 or \
                            len(rule.format_in_f_additional) > 0 and \
                            interpret_comparison(rule.format_in_f_additional[0].subst(subst)):
                        return fls, subst
                    else:
                        continue
            return None

        for rule_i, rule in enumerate(rules):
            t = check_rule(nodes, rule, nodel_mask)
            if t is not None:
                matching_ids, subst_dict = t
                return rule_i, matching_ids, subst_dict

        return None

    def get_open_branches_r(self):
        if len(self.childs) == 0:
            if self.closed:
                return [None]
            else:  # opened
                return [[]]
        else:  # if len(self.childs)==1:
            p = []
            if isinstance(self.formula, EstForm) and isinstance(self.formula.expr, AtomForm):
                p = [self.formula]
            r = []
            for i in range(len(self.childs)):
                r.extend([x for x in self.childs[i].get_open_branches_r() if x is not None])
            sr = [p + l for l in r]
            return sr

    def get_open_branches(self):
        r = self.get_open_branches_r()
        return list(set([tuple(x) for x in r]))


def build_full_tree(formulas):
    formulas = formulas.copy()

    '''
    1. выбираем формулу(ы) и правило
    2. применяем правило
    3. достраиваем дерево
    4. алгоритм рекурсивный
    '''
    tree = atree(formulas)

    tree.build()

    return tree


invsigntable = {'>=': '<',
                '>': '<=',
                '<=': '>',
                '<': '>='}


def get_nodes(ob):
    res = []
    for br in ob:
        for est in br:
            invsign = invsigntable[est.cmpsign]
            res.append((est.expr, invsign))
    res = list(set(res))
    return [x for x in res if 'p' in str(x[0])], [x for x in res if 'q' in str(x[0])]


def get_covers(branches, nodes):
    res = {}
    for i, b in enumerate(branches):
        for j, n in enumerate(nodes):
            corr = None
            for est in b:
                if est.expr == n[0] and n[1] == invsigntable[est.cmpsign]:
                    res[(i, j)] = est.est
    return res


def cover(ct, l1, l2, method=1):
    import numpy as np
    res = []
    succesful = False
    if method == 1:
        # greedy algorithm, sensitive to index permutation
        ids1 = list(range(l1))
        ids2 = list(range(l2))
        while len(ids1) > 0:
            mx = np.zeros([len(ids1), len(ids2)], int)

            for i, k in enumerate(ids1):
                for j, l in enumerate(ids2):
                    if (k, l) in ct:
                        mx[i, j] = 1
            # выбираем столбец с наибольшим количеством единиц
            sums = mx.sum(axis=0)
            sel_j = np.argmax(sums)
            sel_l = ids2[sel_j]
            res.append(sel_l)
            tids1 = ids1.copy()
            for i, k in enumerate(tids1):
                if mx[i, sel_j] == 1:
                    ids1.remove(k)
            ids2.pop(sel_j)
        succesful = len(ids1) == 0
    if method == 2:
        # полный перебор
        a = [[0, 1]] * l2
        tab = []
        from itertools import product
        for t in product(*a):
            covers = None
            # check for selected items cover all left nodes
            # if sum(t)==0:
            #     covers=0
            # else:
            s = {j for j in range(l2) if t[j] == 1}
            u = set()
            for j in s:
                for i in range(l1):
                    if (i, j) in ct:
                        u.add(i)
            covers = len(u)

            l = np.sum(t)
            tab.append((t, (l, covers)))
        tab1=sorted([x for x in tab if x[1][1]==l1],key=lambda x:x[1][0])
        if len(tab1)>0:
            succesful=True
            res=[j for j in range(l2) if j in tab1[0][0]]
        else:
            succesful=False
            res=None
    return res, succesful

def find_estimates(l,r,rCovEsts,cover):
    #rs=[r[i] for i in cover]
    res=[]

    for j,re in enumerate(cover):
        rt=r[re]
        subset=[rCovEsts[i,j] for i in range(len(l)) if (i,j) in rCovEsts]
        if rt[1] in ['>','>=']:
            e=max(subset)
        else:
            e = min(subset)
        res.append(EstForm(rt[0],rt[1],e))

    return res

def get_tree():
    formulas = '(q1=>(~p1&(~p2&(p3&p5))));((~p1&(~p2&(p3&p5)))=>q1);((p2&p4)>=0.3);((p2&p4)<=0.3);(~(q1&q3)>=0.6);((q3>=0.9)=>((~p1>=0.7)&((~p3>=0.2)&(p5>=1))))'.split(
        ';')

    parser = make_estimates_parser()
    fl = [parse_formula(parser, formula) for formula in formulas]
    print(str(fl))
    tree = build_full_tree(fl)
    dct = tree.to_dict()

    open_branches = tree.get_open_branches()

    pnodes, qnodes = get_nodes(open_branches)

    pnodes = sorted(pnodes, key=str)
    qnodes = sorted(qnodes, key=str)  # [::-1]

    pcovers = get_covers(open_branches, pnodes)
    qcovers = get_covers(open_branches, qnodes)

    # using p nodes to cover branches
    cover_set, completed = cover(qcovers, len(open_branches), len(qnodes), method=2)

    ests=[]
    if completed:
        ests=find_estimates(open_branches,qnodes,qcovers,cover_set)

    return dct


if __name__ == '__main__':
    import cProfile

    cProfile.run("get_tree()", filename=None, sort=-1)
