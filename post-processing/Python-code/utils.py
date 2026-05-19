
# construct upa assignments starting from ua and pa assignments
def build_upa(ua, pa):
    upa = dict()
    for u, roles in ua.items():
        upa[u] = set()
        for r in roles:
            upa[u].update(pa[r])

    return upa


# load (ua, pa) from a file having the format as
# Role 3 Capabilities: 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24    # define pa
# Users: 3 4 8 9                                                         # define ua
def load_ua_pa(decomposition):
    ua = dict()
    pa = dict()

    with open(decomposition, 'r') as f:
        for line in f:
            line = line.strip()
            if 'Role' in line:
                role = int(line.split(' ')[1])
                #print('Role: ', role)

            if 'Capabilities' in line:
                permissions = line.split(':')[1].strip()
                pa[role] = set(map(int, permissions.split(' ')))
                #print('Permissions: ', pa[role])

            if 'Users' in line:
                users = line.split(':')[1].strip()
                users = set(map(int, users.split(' ')))
                #print('Users: ', users)

                for user in users:
                    if user not in ua:
                        ua[user] = set()
                    ua[user].add(role)

    return ua, pa


def wsc(ua, pa):
    nr_roles = len(pa.keys())
    ua_size = sum(map(len, ua.values()))
    pa_size = sum(map(len, pa.values()))
    return nr_roles + ua_size + pa_size

# SIMILARITY MEASURES
def compute_sim(roles_a, roles_b):  # roles_a and roles_b are represented by the pa matrix (dictionary of sets)
    sim = 0
    for r_a in roles_a.values():
        s = 0  # intersection size
        for r_b in roles_b.values():
            if (t_s := len(r_a.intersection(r_b)) / (len(r_a.union(r_b)))) > s:
                # s = len(r_a.intersection(r_b))/(len(r_a.union(r_b)))
                s = t_s

        sim += s
    return sim / len(roles_a)


def jaccard(roles_a, roles_b):  # roles_a and roles_b are represented by the pa matrix (dictionary of sets)
    c = 0  # intersection size
    for role in roles_a.values():
        if role in roles_b.values():
            c += 1

    return c / (len(roles_a) + len(roles_b) - c), c


# returns True if the candidate role to_add is not contained nor contains any other constraint in cp
def well_defined(to_add, cp):
    for c in cp:
        if to_add <= c or c <= to_add:
            return False

    return True


# return True if the roles satisfy the family of constraints cp
def satisfy(pa, cp):
    for c in cp:
        for role in pa.values():
            if c <= role:
                return False
    return True


# return True if upa computed from ua and pa is consistent with cp
# consistent: there is at least a user possessing all permissions in some constraint
def check_cp(ua, pa, cp):
    upa = build_upa(ua, pa)
    for permissions in upa.values():
        if any(c <= permissions for c in cp):
            return True

    return False


## utilities for RMPlib datasets

def convert(dataset, folder_in, folder_out):
    print('input  file: ',folder_in+dataset)
    output_file = folder_out + dataset.split('.')[0] + '_converted.txt'
    print('output file: ', output_file)

    with open(folder_in+dataset, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            line = line.strip()
            if line and line[0] == 'u':
                assignements = line.split('\t')
                user = int(assignements[0][1:]) + 1
                print(user, '-->', end=' ')
                for p in assignements[1:]: # for all permissions
                    permission = int(p[1:]) + 1
                    print(permission, end=' ')
                    f_out.write('      ' + str(user) + '      ' + str(permission) + '\n')
                print()

    print('DONE!')

if __name__ == '__main__':
    """
    dataset = 'datasets/optimal_decompositions/'
    name = 'hc'
    suffix = '_exact_cover.txt'
    print('dataset name: ', dataset+name+suffix)
    ua, pa = load_ua_pa(dataset+name+suffix)
    print('ua: ', ua)
    print('pa: ', pa)
    """

    folder_in = 'datasets/RMPlib/original/'
    folder_out = 'datasets/RMPlib/converted/'
    dataset = 'PLAIN_medium_06.rmp'
    convert(dataset, folder_in=folder_in, folder_out=folder_out)
