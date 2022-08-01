try:
    from .estimates import *
except ImportError as e:
    from estimates import *

try:
    from .inference import *
except ImportError as e:
    from inference import *

parser = make_estimates_parser()


def parse_list(l: list, reduce=False):
    res = [parse_formula(parser, s) for s in l]
    if reduce:
        res = [x.reduce() for x in res]
    return res


def test_abduce(tkb, tobs):
    print('абдукция методом аналитических таблиц')
    kb = parse_list(tkb)
    print('база знаний: ', kb)
    observation = parse_list(tobs)
    print('Наблюдение:', observation)

    print('открытые ветви АТ БЗ (C):')
    skb1 = atables_open_branches(kb)
    # for b in skb1:
    #     b.sort(key=lambda x: str(x))
    # skb1.sort(key=lambda x: str(x),reverse=True)
    for b in skb1:
        print('\t', b)

    print('открытые ветви АТ БЗ (C) с учётом поглощений:')
    skb1simp = simplify(skb1)
    for b in skb1simp:
        print('\t', b)

    # print('дизъюнкты БЗ (C):')
    # skb2 = KB2DNF([x.reduce() for x in kb])
    # for b in skb2: print('\t', b)
    # print('дизъюнкты БЗ (C) с учётом поглощений:')
    # skb2simp = simplify(skb2)
    # for b in skb2simp: print('\t', b)

    def make_binsets(names):
        return [(AtomForm(n), '>=') for n in names] + [(AtomForm(n), '<=') for n in names]

    obs = make_binsets(['p1', 'p2', 'p3'])
    print('Атомы - наблюдения (P):', obs)
    abd = make_binsets(['q1', 'q2', 'q3'])
    print('Атомы - абдуценты (Q):', abd)

    graph = build_graph(obs, skb1simp, abd)
    print('Граф покрытий:')
    for e in graph: print('\t', e)

    print('Абдукция по графу')
    negobs = [NegForm(x) for x in observation]
    hyps = abduce_by_graph(graph, negobs, abd)
    print(hyps)

    return hyps

if __name__ == '__main__':
    # print('======================================== ТЕСТ 1 ========================================')
    # print('доказательство формулы методом аналитических таблиц')
    # f = Form.Parse('((p=>(q=>r))=>((p=>q)=>(p=>r)))')
    # ob = atables_open_branches([NegForm(f)])
    # if len(ob) == 0:
    #     print(f, 'общезначима')
    # else:
    #     print(f, 'противоречива')


    print('=' * 10 + ' ТЕСТ 1 ' + '=' * 10)
    test_abduce([
        '~q3=>~q1>=0.5',
        'q1=>~p1&p3&p2>=0.6',
        '~p1&p3&p2=>q1>=0.6',
        'q2=>p1&(p2|~p3)>=0.7',
    ],
        ['p1<=0.9', 'p3>=1'])

    test_abduce(['q1=>p1&p2&~p3>=0.8',
                 'p1&~p2&~p3=>q1<1',
                 'q2=>p1&p3>=0.',
                 'q3=>q2<=0'],

                ['p1>0.9', 'p3>=1'])
    test_abduce(['q1=>p1&p2&~p3>=0.8',
                 'p1&~p4=>q1>=0.9',
                 '+~q2|q3>=0.6=>p1>=0.7'],
                ['p1>0.9', 'p3>=1'])

    # print('\n' * 2)
    # print('======================================== ТЕСТ 2 ========================================')
    # test_abduce(['q1=>p1&&p2&&!p3', 'p1&&p2&&!p3=>q1', 'q2=>p1&&p3', 'q3=>q2', 'q1||q2=>!q3'], ['p1', 'p3'])
    #
    # print('\n' * 2)
    # print('======================================== ТЕСТ 3 ========================================')
    # test_abduce(['q1=>p1&&p2&&!p3', 'p1&&!p4=>q2', '!q2||q3=>!p4'], ['p1', 'p3'])
