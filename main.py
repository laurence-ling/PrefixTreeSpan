from database import *
import time

count = 0


def read_file(path):
    originDB = []
    f = open(path, 'r')
    for line in f.readlines():
        line = line.strip().split()
        originDB.append(Record(line))
    return originDB


def find_freq_label(originDB, min_sup):
    freq_dist = defaultdict(int)
    for record in originDB:
        for label in record.line:
            if label != -1:
                freq_dist[label] += 1
    freq_label = [key for key, val in freq_dist.items()
                  if val >= min_sup]
    return freq_label


def construct_first_order_db(pattern, originDB):
    """
    为一个个label产生一阶投影数据库
    :param pattern: 一阶频繁项
    :param originDB: 原始数据库
    :return: ProjectDB实例
    """

    proDB = ProjectDB(pattern)
    label = pattern.line[0]
    for tid, record in enumerate(originDB):
        for i, cur in enumerate(record.line):
            if cur == label:
                instance = ProjectInstance(tid, [i])
                proDB.instances.append(instance)
    return proDB


def prefix_span(n, pattern_tree, proDB, originDB, min_sup):
    global count
    count += 1
    proDB.find_all_GE(originDB)  # find all legal growth elements
    freq_GEs = [key for key, val in proDB.GEs.items()  # filtering frequent GE
                if val >= min_sup]
    # print(n, 'freq_ge size:', len(freq_GEs), freq_GEs)
    for ge in freq_GEs:
        # generate projected db for each ge
        new_pattern_tree, new_proDB = proDB.generate_projected(ge, originDB)
        # recursively mining next step
        prefix_span(n+1, new_pattern_tree, new_proDB, originDB, min_sup)


def _main(msp):
    global count
    count = 0
    t1 = time.time()
    originDB = read_file('D:\expr\\treedata\\D10.data')
    db_size = len(originDB)
    min_sup = int(db_size * msp)
    print('database size: {}, min_sup: {}'.format(db_size, min_sup))
    freq_label = sorted(find_freq_label(originDB, min_sup))
    print('frequent label size:', len(freq_label))

    for i, label in enumerate(freq_label):
        # print(i, label)
        pattern_tree = Record([label, -1])
        proDB = construct_first_order_db(pattern_tree, originDB)
        prefix_span(1, pattern_tree, proDB, originDB, min_sup)

    t2 = time.time()
    print('runtime:{}'.format(t2-t1))
    print('count:', count)


if __name__ == '__main__':
    min_sup_percent = [0.01, 0.008, 0.006, 0.004, 0.002]
    for msp in min_sup_percent:
        _main(msp)
