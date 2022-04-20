# from log_sys_backend.logic\
from .estimates import *

from collections import defaultdict


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

    # def __repr__(self):
    #     return str([self.format_in, self.format_out_f])

    # def try_to_match(self, flist, pattern=None):
    #     if pattern is None:
    #         pattern = self.format_in_f
    #     if len(pattern) == 1:
    #         # если в шаблон - только на 1 формулу, просто перебираем формулы и применяем правило, если нашлось соответствие
    #         for sf in flist:
    #             t = self.try_to_match_one_formula(sf, pattern[0])
    #             if t is not None:
    #                 return t
    #         return None
    #
    #     if len(pattern) >= 2:
    #         dummies_matching_dict = {}  # подстановка, при применении которой к шаблону получаем формулу
    #         if len(pattern) != len(flist):
    #             return None
    #
    #         for pattern_part, f in zip(pattern, flist):
    #             x = self.try_to_match_one_formula(f.formula, pattern_part)
    #             if x is None:
    #                 return None
    #             # update dict properly
    #             for k in x:
    #                 if not k in dummies_matching_dict:
    #                     dummies_matching_dict[k] = x[k]
    #                 else:
    #                     if dummies_matching_dict[k] != x[k]:
    #                         return None
    #             # dummies_matching_dict.update(x)
    #         for addcnd in self.format_in_f_additional:
    #             a = addcnd.subst(dummies_matching_dict)
    #             if not interpret_comparison(a):
    #                 return None
    #         return dummies_matching_dict

    def apply(self, dummies_matching_dict):
        if self.format_out_f is None:
            return None
        res = [[m.subst(dummies_matching_dict) for m in bs] for bs in self.format_out_f]
        return res

    def __str__(self):
        return '{} & {} |-> {}'.format(self.format_in_f, self.format_in_f_additional, self.format_out_f)


def try_to_match_one_formula(sf, pattern):
    # возвращает подстановку, если формула подходит под шаблон, и None в противном случае

    #вот стоило эту функцию сделать функцией, а не методом класса, вместо 150 секунд выполнение сократилось до 0.5.

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
            print()
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

    # правила выявления замыканий

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

# region atable nodes classes

'''

чем характеризуются вершины дерева?
1. номер шага алгоритма, породивший формулу, 0 для предпосылки
2. идентификатор правила

открытая ветвь:
3. сквознй номер

вершина с формулой
4. результирующая формула
5. ид формулы
6. шаги, где она использована

'''

# endregion


"""
функция построения дерева аналитической таблицы.
для данного префикса ветви находит дерево - суффикс
префикс делится на 2 части:
- подлежащие обработке правилами формулы
- текущее множество литералов

алгоритм:
1) пока во множестве формул есть литералы, перекладывать их во множество литералов
2) если множество формул пусто, и среди литералов нет противоречий - ветвь открыта, вернуть специальный символ (O)
3) если множество литералов противоречиво - вернуть специальный символ (X), обозначающий замкнутую ветвь
4) в противном случае:
  1) выбрать правило (по эвристике или по порядку)
  2) применить правило, получить элементарные суффиксы для новых ветвей
  3) рекурсивно построить новые ветви, а из них - текущее поддерево
  4) вернуть поддерево

:param formulas: подлежащие разбору формулы
:param liters: текущее множество литералов
:param k: счётчик для нумерации узлов дерева - обозначения, какая формула в узле раскрыта
:return: 
"""


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


'''
это дерево - аналитическая таблица.
сначала, вставляются узлы с предпосылками - через конструктор.
всё остальное генерируется рекурсивно при запуске метода build
этот метод поддерживает контекст - список всех родительских узлов с метками о том, какие из них ранее в этой ветви уже были использованы.
'''

from itertools import product


# TODO: решить проблему с производительностью и потреблением памяти
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

        print(branch_prefix)

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
            # 2. если не подобрали - среди всех формул
            # print('TODO: ДОПУСКАЕТСЯ ЛИ ПОСТОРНОЕ ИСПОЛЬЗОВАНИЕ УЗЛОВ В ОДНОЙ ВЕТВИ?')
            # if t is None:
            #     t = self.select_action(branch_prefix, [1] * len(branch_prefix), rules)
            #     if t is not None:
            #         rule_i, matching_ids, subst_dict = t
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

        # def generate_substitutions_rec(k, n_list):
        #     if k == 1:
        #         return [[x] for x in n_list]
        #     ress = []
        #     for e in n_list:
        #         t = n_list.copy()
        #         t.remove(e)
        #         ress.extend([[e] + x for x in generate_substitutions_rec(k - 1, t)])
        #     return ress

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
            #####################################################################################################################################
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


def get_tree():
    # formulas = [
    #     '(q1=>(~p1&(~p2&(p3&p5))))',
    #     '((~p1&(~p2&(p3&p5)))=>q1)',
    #     '((p2&p4)>=0.3)',
    #     '((p2&p4)<=0.3)',
    #     '(~(q1&q3)>=0.6)',
    #     '((q3>=0.9)=>((~p1>=0.7)&((~p3>=0.2)&(p5>=1))))'
    # ]
    formulas = '(q1=>(~p1&(~p2&(p3&p5))));((~p1&(~p2&(p3&p5)))=>q1);((p2&p4)>=0.3);((p2&p4)<=0.3);(~(q1&q3)>=0.6);((q3>=0.9)=>((~p1>=0.7)&((~p3>=0.2)&(p5>=1))))'.split(
        ';')

    parser = make_estimates_parser()
    fl = [parse_formula(parser, formula) for formula in formulas]
    print(str(fl))
    tree = build_full_tree(fl)
    dct = tree.to_dict()
    return dct


if __name__ == '__main__':
    import cProfile

    cProfile.run("get_tree()", filename=None, sort=-1)
    # t = get_tree()

    # import random
    # import winsound
    #
    # for _ in range(30):
    #     f = int(random.uniform(1024, 4096))
    #     winsound.Beep(f, 450)
