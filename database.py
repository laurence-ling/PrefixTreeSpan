from collections import defaultdict


class Record:
    """ 原始数据库中的一条记录
        包含原始的一行string表示，including -1 tag. 每个结点用其索引作为id
        并计算每个结点的partner，用来表示该结点范围
        每个结点的children，方便进行induced subtree扩展
    """
    def __init__(self, line):
        self.line = [int(ele) for ele in line]
        self.partner, self.child_list = self.compute_scope()

    def compute_scope(self):
        label_stack = []
        scope_list = {}  # label index: int -> R, close interval including -1 tag
        child_list = defaultdict(list)  # index -> [] direct children list
        for i, ele in enumerate(self.line):
            if ele != -1:
                label_stack.append(i)
            else:
                start = label_stack.pop()
                scope_list[start] = i
                if len(label_stack) > 0: # not the root node
                    father = label_stack[-1]
                    child_list[father].append(start)
        if len(label_stack) != 0:
            raise ValueError("record line in bad format %s" % self.line)
        return scope_list, child_list


class ProjectInstance:
    """ 投影数据库中的一个实例
        tid: 来自于原始数据库中的哪条记录
        pattern_tree_nodes: 记住产生该模式的所有结点，便于寻找GE
    """
    def __init__(self, tid, node_list):
        self.tid = tid
        self.pattern_tree_nodes = node_list  # pre-order tree nodes index list

    def get_scope(self, record, pos=0):
        """
        计算tree上pos位置结点的scope，注意该实例的最大范围为根节点的partner
        :param record: 原始记录
        :param pos: 前序中第pos个结点
        :return: [L, R]
        """
        root = self.pattern_tree_nodes[pos]
        last = self.pattern_tree_nodes[-1]
        r = record.partner[root]
        return last, r


class ProjectDB:
    """ 投影数据库类
        pattern_tree: 对应的频繁模式
        instances: 一条ProjectInstance
        GEs: 所有 legal growth elements 及其计数
    """
    def __init__(self, pattern_tree):
        self.pattern_tree = pattern_tree
        self.instances = []
        self.GEs = {}

    def extend_pattern(self, ge):
        label, pos = ge
        cnt, end = -1, 0
        for i, node in enumerate(self.pattern_tree.line):
            if node == -1:
                continue
            cnt += 1
            if cnt == pos:
                end = self.pattern_tree.partner[i]  # -1 tag position
                break
        x = self.pattern_tree.line[:]
        x.insert(end, label)
        x.insert(end+1, -1)
        new_pattern = Record(x)
        return new_pattern

    def generate_projected(self, ge, originDB):
        # extend pattern tree
        ext_pattern_tree = self.extend_pattern(ge)
        proDB = ProjectDB(ext_pattern_tree)
        label, pos = ge
        # generate projected db
        for instance in self.instances:
            tid = instance.tid
            record = originDB[tid]
            father = instance.pattern_tree_nodes[pos]
            L, R = instance.get_scope(record, pos)
            # for index in range(L+1, R):
            for index in record.child_list[father]:
                if index <= L or index >= R:
                    continue
                if record.line[index] == label:
                    new_node_list = instance.pattern_tree_nodes[:]  # note: copy list
                    new_node_list.append(index)
                    proDB.instances.append(ProjectInstance(tid, new_node_list))
                    break
        return ext_pattern_tree, proDB

    def find_all_GE(self, originDB):
        GE_dict = defaultdict(int)
        for instance in self.instances:
            tid = instance.tid
            record = originDB[tid]
            L, R = instance.get_scope(record)
            for i in range(L+1, R):
                #  each label could be a GE
                label = record.line[i]
                if label == -1:
                    continue
                # for embedded subtree, can attach to its ancestor node
                # pos = self.get_GE_ancestor_node(record.partner, instance.pattern_tree_nodes, i)
                # for induced subtree, only attach to its parent node
                pos = self.get_GE_father_node(record.child_list, instance.pattern_tree_nodes, i)
                if pos != -1:
                    GE_dict[(label, pos)] += 1
        self.GEs = GE_dict

    def get_GE_ancestor_node(self, partner, pattern_nodes, index):
        father = -1
        # find the last label matched to be the ancestor
        for i, node in enumerate(pattern_nodes):
            s_L, s_R = node, partner[node]
            if s_L < index <= s_R:
                father = i
        if father == -1:
            raise ValueError("GE has no parent node.")
        return father

    def get_GE_father_node(self, child_list, tree_nodes, index):
        for i, node in enumerate(tree_nodes):
            if node not in child_list.keys():
                continue
            if index in child_list[node]:
                return i
        return -1
