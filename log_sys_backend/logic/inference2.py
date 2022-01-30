# from log_sys_backend.logic\
from .estimates import *


class infrule:
    def __init__(self, format_in, format_out, priority):
        ep = make_estimates_parser()
        self.format_in = format_in
        self.format_in_f = [parse_formula(ep, x) for x in format_in]
        self.format_out = format_out
        if format_out is not None:
            self.format_out_f = [[parse_formula(ep, pf) for pf in l] for l in format_out]
        else:
            self.format_out_f = None
        self.priority = priority

    def try_to_match(self, flist, pattern=None):
        dummies_matching_dict = {}
        if pattern is None:
            pattern = self.format_in_f
        if len(flist) == 1 and len(pattern) == 1:
            # region simple case: 1 formula and 1 rule
            fl = flist[0]
            sr = pattern[0]
            if isinstance(sr, RuleDummyForm):
                return {sr.name: fl}
            if not isinstance(fl, type(sr)):
                return None
            # types are same. matching childs
            if isinstance(fl, (ConForm, DisForm)):
                if len(fl.members) != len(sr.members):
                    # match first elements and then second to last with second rule member
                    t1 = self.try_to_match([fl.members[0]], [sr.members[0]])
                    if t1 is None:
                        return None
                    dummies_matching_dict.update(t1)
                    fld = (ConForm if isinstance(fl, ConForm) else DisForm)(fl.members[1:])
                    t2 = self.try_to_match([fld], [sr.members[1]])
                    if t2 is None:
                        return None
                    dummies_matching_dict.update(t2)
                else:
                    for i in range(len(fl.members)):
                        t = self.try_to_match([fl.members[i]], [sr.members[i]])
                        if t is None:
                            return None
                        dummies_matching_dict.update(t)
                return dummies_matching_dict

            elif isinstance(fl, NegForm):
                return self.try_to_match([fl.value], [sr.value])
            elif isinstance(fl, ImpForm):
                t1 = self.try_to_match([fl.a], [sr.a])
                if t1 is None:
                    return None
                t2 = self.try_to_match([fl.b], [sr.b])
                if t2 is None:
                    return None
                dummies_matching_dict.update(t1)
                dummies_matching_dict.update(t2)
                return dummies_matching_dict
            elif isinstance(fl, EstForm):
                if fl.cmpsign != sr.cmpsign:
                    return None
                if isinstance(sr.est, RuleDummyForm):
                    dummies_matching_dict[sr.est.name] = fl.est
                elif isinstance(sr.est, float):
                    if sr.est != fl.est:
                        return None
                else:
                    print()
                t = self.try_to_match([fl.expr], [sr.expr])
                if t is None:
                    return None
                dummies_matching_dict.update(t)
                return dummies_matching_dict
            else:
                print()
            # endregion
        elif len(flist) == 1:
            return None
        else:
            if len(pattern) == 1:
                for sf in flist:
                    t = self.try_to_match([sf], pattern)
                    if t is not None:
                        return t
                return None
            # print('OOO', flist, pattern)
            add_condition = None
            if len(pattern) > 2:
                add_condition = pattern[2]
                pattern = pattern[:2]

            pattern_signs = [sp.cmpsign for sp in pattern]
            cfl = flist.copy()

            matching = []
            for i, csign in enumerate(pattern_signs):
                for f in cfl:
                    if f.cmpsign == csign and f not in matching:
                        matching.append(f)
                        break
            if len(matching) != len(pattern_signs):
                return None

            for f, p in zip(matching, pattern):
                t = self.try_to_match([f], [p])
                if t is None:
                    return None
                else:
                    dummies_matching_dict.update(t)

            if add_condition is not None:
                cond = False
                if add_condition.cmpsign == '<':
                    cond = dummies_matching_dict[add_condition.expr.name] < dummies_matching_dict[
                        add_condition.est.name]
                elif add_condition.cmpsign == '<=':
                    cond = dummies_matching_dict[add_condition.expr.name] <= dummies_matching_dict[
                        add_condition.est.name]
                elif add_condition.cmpsign == '>':
                    cond = dummies_matching_dict[add_condition.expr.name] > dummies_matching_dict[
                        add_condition.est.name]
                elif add_condition.cmpsign == '>=':
                    cond = dummies_matching_dict[add_condition.expr.name] >= dummies_matching_dict[
                        add_condition.est.name]
                if cond:
                    return dummies_matching_dict, matching
                else:
                    return None
            # print(self, flist, matching)
            return dummies_matching_dict, matching

    def apply(self, dummies_matching_dict):
        if self.format_out_f is None:
            return None
        res = [[m.subst(dummies_matching_dict) for m in bs] for bs in self.format_out_f]
        return res

    def __str__(self):
        return '{} |-> {}'.format(self.format_in_f, self.format_out_f)


rules_base = [
    [['~~A'], [['A']], 2],
    [['(A&B)'], [['A', 'B']], 2],
    [['~(A&B)'], [['~A'], ['~B']], 1],
    [['(A|B)'], [['A'], ['B']], 1],
    [['~(A|B)'], [['~A', '~B']], 2],
    [['(A=>B)'], [['~A'], ['B']], 1],
    [['~(A=>B)'], [['A', '~B']], 2],

    [['~(A>=X)'], [['A<X']], 2],
    [['~(A>X)'], [['A<=X']], 2],
    [['~(A<=X)'], [['A>X']], 2],
    [['~(A<X)'], [['A>=X']], 2],

    [['(~A)>=X'], [['A<=1-X']], 2],
    [['(~A)>X'], [['A<1-X']], 2],
    [['(~A)<=X'], [['A>=1-X']], 2],
    [['(~A)<X'], [['A>1-X']], 2],

    [['(A&B)>=X'], [['A>=X', 'B>=X']], 2],
    [['(A&B)>X'], [['A>X', 'B>X']], 2],
    [['(A&B)<=X'], [['A<=X'], ['B<=X']], 1],
    [['(A&B)<X'], [['A<X'], ['B<X']], 1],

    [['(A|B)>=X'], [['A>=X'], ['B>=X']], 1],
    [['(A|B)>X'], [['A>X'], ['B>X']], 1],
    [['(A|B)<=X'], [['A<=X', 'B<=X']], 2],
    [['(A|B)<X'], [['A<X', 'B<X']], 2],

    [['(A=>B)>=X'], [['A<=1-X'], ['B>=X']], 1],
    [['(A=>B)>X'], [['A<1-X'], ['B>X']], 1],
    [['(A=>B)<=X'], [['A>=1-X', 'B<=X']], 2],
    [['(A=>B)<X'], [['A>1-X', 'B<X']], 2],

    [['A<=X', 'A<=Y'], [['A<=min(X,Y)']], 3],
    [['A<=X', 'A<Y'], [['A<min(X,Y)']], 3],
    [['A<X', 'A<Y'], [['A<min(X,Y)']], 3],

    [['A>=X', 'A>=Y'], [['A>=max(X,Y)']], 3],
    [['A>=X', 'A>Y'], [['A>max(X,Y)']], 3],
    [['A>X', 'A>Y'], [['A>max(X,Y)']], 3],

    [['A>1'], None, 4],
    [['A<0'], None, 4],
    [['A>=X', 'A<=Y', 'X>Y'], None, 4],
    [['A>X', 'A<=Y', 'X>=Y'], None, 4],
    [['A>X', 'A<Y', 'X>=Y'], None, 4],
    [['A>X', 'A<Y', 'X>Y'], None, 4],

    # [['A'], [['A>=1']], 0],
    # [['~A'], [['A<=0']], 0],
]

rules = [infrule(x[0], x[1], x[2]) for x in rules_base]

rules = sorted(rules, key=lambda x: x.priority, reverse=True)


# region atable nodes classes
class atable_tree_node:

    def __repr__(self):
        raise NotImplementedError()

    def to_dict(self):
        return {'error': 'not implemented'}


class atable_tree_node_opened_end(atable_tree_node):
    def __repr__(self):
        return '(O)'

    def __str__(self):
        return '(O)'

    def to_dict(self):
        return {'name': '(O)', 'children': []}


class atable_tree_node_closed_end(atable_tree_node):
    def __repr__(self):
        return '(X)'

    def __str__(self):
        return '(X)'

    def to_dict(self):
        return {'name': '(X)', 'children': []}


class atable_tree_node_usual(atable_tree_node):
    def __init__(self, formula: str, formula_index: int, childs: list):
        self.formula = formula
        self.childs = childs
        self.formula_index = formula_index

    def __repr__(self):
        return '{} [{}]'.format(self.formula, self.formula_index)

    def __str__(self):
        return '{} [{}]'.format(self.formula, self.formula_index)

    def to_dict(self):
        return {'name': '{} [{}]'.format(self.formula, self.formula_index),
                'children': [x.to_dict() for x in self.childs]}


# endregion

def is_literal(f: Form):
    if isinstance(f, EstForm) and isinstance(f.expr, AtomForm):
        return True
    else:
        return False


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


def literals_have_contradiction(literals):
    return False


def build_full_tree_v3(formulas, literals=None):
    '''
    имеем список формул.
    имеем словарь литер.
    если есть противоречивые литеры - ветвь замкнута.
    иначе, если есть правило, применимое к литерам - применяем это правило (рекурсия)
    иначе, если есть правило, применимое к формулам - применяем это правило (рекурсия)
    иначе, если список правил пуст, и среди длитер нет противоречий, ветвь - открыта.

    :param formulas:
    :param literals:
    :return:
    '''
    if literals is None:
        literals = {}
    formulas = formulas.copy()
    # region перемещаем формулы-литералы в словарь литералов
    for formula in formulas:
        if is_literal(formula):
            formulas.remove(formula)
            nliterals = literals.copy()
            if formula.expr.name in nliterals:
                nliterals[formula.expr.name].append(formula)
            else:
                nliterals[formula.expr.name] = [formula]
            tr = build_full_tree_v3(formulas, nliterals)
            return atable_tree_node_usual(str(formula), 0, [tr])
    # endregion
    # region проверяем, что есть противоречивые литеры
    contra_rule_i = None
    contra_literals = None
    for j, rule in enumerate(rules):
        if rule.priority != 4:
            continue
        for varname in literals:
            pdt = rule.try_to_match(literals[varname])
            if pdt is not None:
                matching = pdt[1]
                pd = pdt[0]
                contra_rule_i = j
                contra_literals = matching
                break
        if contra_literals is not None:
            break
    # если есть противоречивые литеры, вернуть замкнутую ветвь
    if contra_literals is not None:
        return atable_tree_node_usual(str(contra_literals), 0, [atable_tree_node_closed_end()])
    # endregion
    # проверяем, что есть формулы, применяемые только к литерам
    literal_rule_i = None
    repl_literals = None
    resvarname = None
    pd = None
    for j, rule in enumerate(rules):
        if rule.priority != 3:
            continue
        for varname in literals:
            pdt = rule.try_to_match(literals[varname])
            if pdt is not None:
                matching = pdt[1]
                pd = pdt[0]
                literal_rule_i = j
                repl_literals = matching
                resvarname = varname
                break
        if repl_literals is not None:
            break
    # если есть - заменяем старые литеры результатом правила, и строим дерево дальше
    if repl_literals is not None:
        nlits = literals.copy()
        nlits[resvarname] = [x for x in nlits[resvarname] if x not in repl_literals]
        new_literals = rules[literal_rule_i].apply(pd)
        nlits[resvarname].extend(new_literals[0])
        return atable_tree_node_usual(str(repl_literals), 0, [build_full_tree_v3(formulas, nlits)])
    # region если список правил не пуст, выбираем наиболее приоритетное правило и применяем его
    if len(formulas) > 0:
        selected_rule_i = None
        selected_formula_i = None
        for j, rule in enumerate(rules):
            if rule.priority >= 3:
                continue
            for i, formula in enumerate(formulas):
                pd = rule.try_to_match([formula])
                # print(rule, formula)
                if pd is not None:
                    selected_rule_i = j
                    selected_formula_i = i
                    break
            if selected_formula_i is not None:
                break

        # применить правило, получить элементарные суффиксы для новых ветвей
        selected_formula = formulas.pop(selected_formula_i)
        possible_branches_starts = rules[selected_rule_i].apply(pd)
        childs = []
        p = 0
        for appendix in possible_branches_starts:
            t = formulas + appendix
            p += 1
            res_br = build_full_tree_v3(t, literals)
            childs.append(res_br)
        result = atable_tree_node_usual(str(selected_formula), 0, childs)
        return result
    # endregion
    # если список правил пуст - ветвь открыта
    return atable_tree_node_opened_end()


# def build_full_tree_v2(available_formulas, literals=None, k=0):
#     if literals is None:
#         literals = {}  # dict: variable name => list of estimates with it
#     else:
#         literals = literals.copy()
#     # 1) пока во множестве формул есть литералы, перекладывать их во множество литералов
#     available_formulas = available_formulas.copy()
#
#     for formula in available_formulas:
#         if is_literal(formula):
#             available_formulas.remove(formula)
#             nliterals = literals.copy()
#             if formula.expr.name in nliterals:
#                 nliterals[formula.expr.name].append(formula)
#             else:
#                 nliterals[formula.expr.name] = [formula]
#             # nliterals
#             tr = build_full_tree_v2(available_formulas, nliterals, k)
#             tr = atable_tree_node_usual(str(formula), k, [tr])
#             return tr
#
#     # 3) если множество литералов противоречиво - вернуть специальный символ (X), обозначающий замкнутую ветвь
#
#     # для этого попытаемся применить формулы к литералам
#
#     selected_rule_i = None
#     selected_literals = None
#     pd = None
#     for j, rule in enumerate(rules):
#         for varname in literals:
#             pd = rule.try_to_match(literals[varname])
#             if pd is not None:
#                 selected_rule_i = j
#                 selected_literals = literals[varname]
#                 break
#         if selected_literals is not None:
#             break
#     if selected_literals is not None:
#         # применить правило, получить элементарные суффиксы для новых ветвей
#         possible_branches_starts = rules[selected_rule_i].apply(pd)
#
#
#     else:  # если в литералах не найдено противоречий
#
#         # # 2) если множество формул пусто, и среди литералов нет противоречий - ветвь открыта, вернуть специальный символ (O)
#         # if len(available_formulas) == 0 and not literals_have_contradiction(literals):
#         #     return atable_tree_node_opened_end()
#
#         # 4) в противном случае:
#         # выбрать правило (по эвристике или по порядку)
#         # предполагается, что правила упорядочены по убыванию приоритета
#         selected_rule_i = None
#         selected_formula_i = None
#         for j, rule in enumerate(rules):
#             for i, formula in enumerate(available_formulas):
#                 pd = rule.try_to_match([formula])
#                 if pd is not None:
#                     selected_rule_i = j
#                     selected_formula_i = i
#                     break
#             if selected_formula_i is not None:
#                 break
#
#         # применить правило, получить элементарные суффиксы для новых ветвей
#         selected_formula = available_formulas.pop(selected_formula_i)
#         possible_branches_starts = rules[selected_rule_i].apply(pd)
#
#     if possible_branches_starts is None:
#         return atable_tree_node_closed_end()
#     elif isinstance(possible_branches_starts, list):
#         childs = []
#         p = k
#         for appendix in possible_branches_starts:
#             t = available_formulas + appendix
#             p += 1
#             res_br = build_full_tree_v2(t, literals, p)
#             childs.append(res_br)
#         result = atable_tree_node_usual(str(selected_formula), k, childs)
#         return result
#     else:
#         return atable_tree_node_opened_end()


def get_tree():
    formula = '~(a>0.1)&(b>=0.3)'
    parser = make_estimates_parser()
    fl = parse_formula(parser, formula)
    print(str(fl))
    tree = build_full_tree_v3([fl])
    return tree.to_dict()

# get_tree()
