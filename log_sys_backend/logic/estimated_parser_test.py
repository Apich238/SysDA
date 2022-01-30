from .estimates import *

parser = make_estimates_parser()


def test(l):
    global s

    print('=' * 80)
    print('=' * 40)
    print(l)
    t = time()
    syntree = parser.Parse(l)
    s += time() - t
    # syntree.TreeRepr()
    print('=' * 40)
    print(l)
    ast = syn2ast(syntree)
    ast.TreeRepr()
    res = compile_ast(ast)
    print(res)


if __name__ == '__main__':
    from time import time

    s = 0

    test_list = ['+p1>=0.7',
                 'q1=>p1&p2&~p3>=0.8',
                 'a&b&c&d&e>0.1',
                 'p1&~~p4=>q1>=0.9',
                 '~q2|q3>=0.6=>p1>=0.7',
                 '~(p1&q3=>~p2<=0.5)=>(p2&~q2>0.9)']

    N = 100
    for i in range(N):
        for fl in test_list:
            test(fl)

    print('average time:', s / (N * len(test_list)))
