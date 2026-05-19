import random
import utils

# generate cp according to four modalities 'upa_rnd', 'upa_small', 'pa_rnd', and 'pa_small'
# constraints are chosen within the relation upa (resp., pa),
# either we select nc random users (resp., roles)
# or we select nc users (resp., roles) with the smallest permission set (in terms of length)
#  In both cases, the constraints are formed considering all the permissions assigned to users (resp., roles).
#  While adding constraints to cp, we must guarantee that the resulting family cp is well-defined
# (i.e. any constraint is not contained nor contains any other constraint in cp).
def generate_cp(relation, nc, modality):
    assert modality in ('random', 'smallest'), 'Unknown modality'
    cp = list()  # list of sets

    if modality == 'random':
        choices = random.sample(list(relation.keys()), len(relation.keys()))  # users permutation
    else:
        choices = list(sorted(relation.keys(), key=lambda u: len(relation[u])))

    for index in choices:
        if len(relation[index]) == 1:
            continue
        if utils.well_defined(relation[index], cp):
            cp.append(relation[index])
        if len(cp) == nc:
            break

    return cp


# generate (ua, pa) as in "Roleminer: mining roles using subset enumeration" Vaidya et al., CCS ’06
def generate_ua_pa(nr, nu, np, mru, mpr):
    ua = {}  # dictionary (user, set of roles)
    pa = {}  # dictionary (role, set of permissions)
    permissions = list(range(1, np + 1))
    roles = list(range(1, nr + 1))
    used_roles = set()
    used_permissions = set()
    role_set = []

    # generate random roles
    # print('generate random roles')
    r = 1
    while r <= nr:
        size_role = random.randint(1, mpr)  # random size
        # size_role = random.randint(mpr//3, mpr)  # random size

        role = set(random.sample(permissions, size_role))  # random permissions
        if role not in role_set:
            role_set.append(role)
            pa[r] = role
            used_permissions.update(role)
            # print(r, pa[r], ' ', len(pa[r]))
            r += 1

    # assign roles to users
    # print('assign roles to users')
    for u in range(1, nu + 1):
        n_r_u = random.randint(1, mru)
        ua[u] = set(random.sample(roles, n_r_u))
        used_roles.update(ua[u])
        # print(u, ua[u], ' ', len(ua[u]))

    # remove from pa un-used roles
    unused_roles = set(roles).difference(used_roles)
    for u_r in unused_roles:
        del pa[u_r]

    # print('u_r', used_roles, len(used_roles), 'expected:', nr)
    # print('un_r', unused_roles)
    # print('u_p', len(used_permissions), 'expected:', np)
    return ua, pa, used_roles, used_permissions


# Generate dataset to be used in the experiments
def generate_dataset(nr, nu, np, mru, mpr, nc, modality='upa_rnd'):
    assert modality in ('upa_rnd', 'upa_small', 'pa_rnd', 'pa_small'), 'Unknown mode'
    #print('Generating (ua, pa, cp)  Mode:', mode)


    ua, pa, _, _ = generate_ua_pa(nr, nu, np, mru, mpr)
    upa = utils.build_upa(ua, pa)

    if modality == 'upa_rnd':
            cp = generate_cp(upa, nc, 'random')
    elif modality == 'upa_small':
            cp = generate_cp(upa, nc, 'smallest')
    elif modality == 'pa_rnd':
            cp = generate_cp(pa, nc, 'random')
    elif modality == 'pa_small':
            cp = generate_cp(pa, nc, 'smallest')
    else:
        raise ValueError('Unknown mode')

    return ua, pa, cp




if __name__ == '__main__':
    nr, nu, np, mru, mpr = 200, 500, 1500, 3, 150
    # nr, nu, np, mru, mpr = 100, 2000, 500, 3, 50

    nc = 4


    gen_methods = 'upa_rnd', 'upa_small', 'pa_rnd', 'pa_small'


    for gen_method in gen_methods:
        ua, pa, cp = generate_dataset(nr, nu, np, mru, mpr, nc, modality=gen_method)
        print(len(ua), len(pa), len(cp))

        print()