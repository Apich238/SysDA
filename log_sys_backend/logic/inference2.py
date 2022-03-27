# from log_sys_backend.logic\
from .estimates import *

from collections import defaultdict


class infrule:
    def __init__(self, format_in, format_out, priority, id):
        ep = make_estimates_parser()
        self.format_in = format_in
        self.id = id
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

    # [['A>1'], None, 4],
    # [['A<0'], None, 4],

    # [['A>=X', 'A<=Y', 'X>Y'], None, 4],
    # [['A>X', 'A<=Y', 'X>=Y'], None, 4],
    # [['A>X', 'A<Y', 'X>=Y'], None, 4],
    # [['A>X', 'A<Y', 'X>Y'], None, 4],

    ['t1r25', ['A', '~A'], None, 4],

    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],
    # ['',[],None,4],

    # [['A'], [['A>=1']], 0],
    # [['~A'], [['A<=0']], 0],
]

rules = [infrule(x[1], x[2], x[3], x[0]) for x in rules_base]

rules = sorted(rules, key=lambda x: x.priority, reverse=True)

# region atable nodes classes

'''

чем характеризуются вершины дерева?
1. номер шага алгоритма, породивший формулу, 0 для предпосылки
2. идентификатор правила

открытая и закрытая ветви:

вершина с формулой
4. результирующая формула

'''


class atable_tree_node:
    def __init__(self, processed_step, created_step, rule_id):
        self.processed_step = processed_step
        self.created_step = created_step
        self.rule_id = rule_id

    def __repr__(self):
        raise NotImplementedError()

    def to_dict(self):
        return {'error': 'not implemented'}


class atable_tree_node_opened_end(atable_tree_node):
    def __init__(self, processed_step, created_step, rule_id):
        super().__init__(processed_step, created_step, rule_id)

    def __repr__(self):
        return '{}:(O)'.format(self.processed_step)

    def __str__(self):
        return '{}:(O)'.format(self.processed_step)

    def to_dict(self):
        return {'name': '{}:(O)'.format(self.processed_step), 'children': []}


class atable_tree_node_closed_end(atable_tree_node):
    def __init__(self, processed_step, created_step, rule_id):
        super().__init__(processed_step, created_step, rule_id)

    def __repr__(self):
        return '{}:(X)'.format(self.processed_step)

    def __str__(self):
        return '{}:(X)'.format(self.processed_step)

    def to_dict(self):
        return {'name': '{}:(X)'.format(self.processed_step), 'children': []}


class atable_tree_node_usual(atable_tree_node):
    def __init__(self, processed_step, created_step, rule_id, formula, childs):
        super().__init__(processed_step, created_step, rule_id)
        self.formula = formula
        self.childs = childs
        self.formula = formula
        self.rule_id = rule_id

    def __repr__(self):
        return '{}:{}'.format(self.processed_step, self.formula)

    def __str__(self):
        return '{}:{}'.format(self.processed_step, self.formula)

    def to_dict(self):
        return {'name': '{}/{}(rule {}):{}'.format(self.processed_step, self.created_step, self.rule_id, self.formula),
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


def build_full_tree(formulas, literals=None, cntr=None, usages=None):
    '''
    имеем список формул, которые можно обработать, и словарь литер.

    литера - оценкаа переменной

    литералы в списке формул перемещаются в словарь литералов

    если есть противоречивые литеры - ветвь замкнута (выход из рекурсии)
    иначе, если есть правило, применимое к литерам - применяем это правило (рекурсия)
    иначе, если есть правило, применимое к формулам - применяем это правило (рекурсия)
    иначе, если список формул пуст, и среди литер нет противоречий, ветвь - открыта.

    :param formulas:
    :param literals:
    :return:
    '''
    if literals is None:
        literals = defaultdict(list)
    if cntr is None:
        cntr = counter()
    if usages is None:
        usages = defaultdict(list)
    formulas = formulas.copy()
    # region перемещаем формулы-литералы в словарь литералов
    for formula in formulas:
        if is_literal(formula):  # выбираем первую формулу - литеру, елси такие есть
            # готовим параметры для рекурсивного вызова.
            # если в ветки есть ещё формулы - литеры, они будут обработаны в рекурсии
            formulas.remove(formula)
            nliterals = literals.copy()  # рвём связь
            nliterals[formula.expr.name].append(formula)
            step = cntr.inc()
            tr = build_full_tree(formulas, nliterals, cntr, usages)
            return atable_tree_node_usual(step, step, 'extract_literal', str(formula), [tr])
    # endregion
    # region проверяем, что есть противоречивые литеры
    contra_rule = None
    contra_literals = None  # литералы, которые сопоставились с шаблоном правила
    for j, rule in enumerate(rules):
        if rule.priority != 4:  # пропускаем правила, не дающие противоречия
            continue
        for varname in literals:  # проходясь по известным именам переменных
            pdt = rule.try_to_match(literals[varname])  # пытаемся сопоставить шаблон и литеры с данной переменной
            if pdt is not None:  # если сопоставилось - оформляем результат
                matching = pdt[1]
                pd = pdt[0]
                contra_rule = rule.id
                contra_literals = matching
                # если есть противоречивые литеры, вернуть замкнутую ветвь
                step = cntr.inc()
                return atable_tree_node_closed_end(step, step, contra_rule)
    # endregion
    # region проверяем, что есть формулы, применяемые только к литерам (формулы сокращений)
    literal_rule_i = None  # индекс правила
    repl_literals = None
    resvarname = None
    pd = None
    for j, rule in enumerate(rules):
        if rule.priority != 3:  # пропускаем ненужные формулы
            continue
        for varname in literals:
            pdt = rule.try_to_match(literals[varname])  # пытаемся сопоставить литеры каждой переменной
            if pdt is not None:  # если что-то сопоставилось - запоминаем это правило, потом применим
                matching = pdt[1]
                pd = pdt[0]
                literal_rule_i = j
                repl_literals = matching
                resvarname = varname
                # если такие есть - заменяем старые литеры результатом правила, и строим дерево дальше
                nlits = literals.copy()
                nlits[resvarname] = [x for x in nlits[resvarname] if x not in repl_literals]
                new_literals = rules[literal_rule_i].apply(pd)
                nlits[resvarname].extend(new_literals[0])
                step = cntr.inc()
                return atable_tree_node_usual(step, step, rules[literal_rule_i].id,
                                              str(new_literals), [build_full_tree(formulas, nlits, cntr, usages)])
    # endregion
    # region если список нераскрытых формул не пуст, выбираем наиболее приоритетное правило и применяем его
    if len(formulas) > 0:
        selected_rule_i = None  # иандекс ыфбранного правила
        selected_formula_i = None  # индекс выбранной формулы
        for j, rule in enumerate(rules):
            if rule.priority >= 3:  # пропускаем правила, отработанные ранее
                continue
            for i, formula in enumerate(formulas):
                pd = rule.try_to_match([formula])
                # print(rule, formula)
                if pd is not None:  # если формула соответствует правилу
                    selected_rule_i = j
                    selected_formula_i = i

                    # применить правило, получить элементарные суффиксы для новых ветвей
                    selected_formula = formulas.pop(selected_formula_i)
                    possible_branches_starts = rules[selected_rule_i].apply(pd)
                    childs = []
                    step = cntr.inc()
                    for appendix in possible_branches_starts:
                        t = formulas + appendix
                        res_br = build_full_tree(t, literals, cntr, usages)
                        childs.append(res_br)
                    result = atable_tree_node_usual(step, step, rules[selected_rule_i].id,
                                                    str(selected_formula), childs)
                    return result
    # endregion
    # если список правил пуст - ветвь открыта
    step = cntr.inc()
    return atable_tree_node_opened_end(step, step, 'all_formulas_used')


def get_tree():
    formula = '~(a>0.1)&(b>=0.3)'
    parser = make_estimates_parser()
    fl = parse_formula(parser, formula)
    print(str(fl))
    tree = build_full_tree([fl])
    return tree.to_dict()

# get_tree()
