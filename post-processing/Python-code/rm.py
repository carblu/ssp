from copy import deepcopy
import abc
import math

class Mining:
    def __init__(self, dataset, unique=False):
        if type(dataset) != str and type(dataset) != dict:
            raise Exception('Dataset error: unknown format')

        self._users = set()
        self._permissions = set()
        self._upa = {}  # dictionary (user, set of permissions)
        self._upa_unique = {}  # dictionary (user, set of permissions) only users with distinct set of permissions
        self._pua = {}  # dictionary (permission, set of users)
        self._ua = {}  # dictionary (user, set of roles)
        self._pa = {}  # dictionary (role, set of permissions)
        self._k = 0  # mined roles so far
        self._n = 0  # total number of granted access to resources (i.e., number of pairs in dataset)

        self._set_dataset(dataset)


        if unique:  # collapse users having the same set of permissions to just one user
            self._unique_users()

        self._unc_upa = deepcopy(self._upa)
        # Be careful, if we compute the cluster, we should recompute pua
        self._unc_pua = deepcopy(self._pua)
        self._unc_users = deepcopy(self._users)
        self._unc_permissions = deepcopy(self._permissions)


    def _set_dataset(self, dataset):
        if type(dataset) == str:
            self._dataset = dataset
            self._load_upa()
        elif type(dataset) == dict:  # the dataset is represented by a dictionary (UPA)
            self._dataset = '-- direct upa inizialization --'
            self._upa = deepcopy(dataset)
            self._users = set(self._upa.keys())
            for u, prms in self._upa.items():
                self._permissions = self._permissions.union(prms)
                self._n += len(prms)
                for p in prms:
                    if p in self._pua:
                        self._pua[p].add(u)
                    else:
                        self._pua[p] = {u}
        else:
            raise Exception('Dataset error: unknown format')


    def _load_upa(self):
        with open(self._dataset) as f:
            for u_p in f:
                (user, permission) = u_p.split()
                user = int(user.strip())
                permission = int(permission.strip())

                if user in self._users:
                    if permission not in self._upa[user]:
                        self._upa[user].add(permission)
                        self._n = self._n + 1
                else:
                    self._users.add(user)
                    self._upa[user] = {permission}
                    self._n = self._n + 1

                if permission in self._permissions:
                    self._pua[permission].add(user)
                else:
                    self._permissions.add(permission)
                    self._pua[permission] = {user}


    def get_upa(self):
        return self._upa

    def get_pa(self):
        return self._pa

    def get_ua(self):
        return self._ua

    # used by the mining algorithms, update ua and pa matrices assinging permissions 'prms' to users 'usrs'
    def _update_ua_pa(self, usrs, prms):
        idx = 0
        if in_pa := [r for (r, role) in self._pa.items() if role == prms]:
            idx = in_pa[0]

        if not idx:
            self._k = self._k + 1
            self._pa[self._k] = deepcopy(prms)
            idx = self._k

        for u in usrs:
            if u in self._ua:
                self._ua[u].add(idx)
            else:
                self._ua[u] = {idx}


    # after a role has been assigned, look for users and permissions not coverd yet
    def _update_unc_c(self, usrs, prms):
        for u in usrs:
            self._unc_upa[u] = self._unc_upa[u] - prms
            if len(self._unc_upa[u]) == 0:
                self._unc_users.remove(u)
        for p in prms:
            self._unc_pua[p] = self._unc_pua[p] - usrs
            if len(self._unc_pua[p]) == 0 and p in self._unc_permissions:
                self._unc_permissions.remove(p)


    # after a role has been assigned, look for users and permissions not coverd yet
    # remove users and permissions covered
    def _update_unc(self, usrs, prms):
        for u in usrs:
            self._unc_upa[u] = self._unc_upa[u] - prms
            if len(self._unc_upa[u]) == 0:
                del self._unc_upa[u]
                self._unc_users.remove(u)
        for p in prms:
            if p in self._unc_pua:
                self._unc_pua[p] = self._unc_pua[p] - usrs
                if len(self._unc_pua[p]) == 0 and p in self._unc_permissions:
                    del self._unc_pua[p]
                    self._unc_permissions.remove(p)

    @abc.abstractmethod
    def _pick_role(self):
        pass

    # mining algorithm
    @abc.abstractmethod
    def mine(self):
        pass


    # remove duplicated users from UPA, results from get_wsc should reflect this 'compression'
    def _unique_users(self):
        self._users_bk = deepcopy(self._users)  # users backup
        self._upa_bk = deepcopy(self._upa)  # upa backup
        self._users_map = dict()  # key = user, value=list of users with identical permissions
        equal_prms = dict()
        for u in self._users:
            equal_prms[u] = u
        self._upa = dict()

        for u_i in sorted(self._upa_bk.keys()):
            for u_j in sorted(self._upa_bk.keys()):
                if u_j > u_i and equal_prms[u_j] == u_j and self._upa_bk[u_j] == self._upa_bk[u_i]:
                    equal_prms[u_j] = u_i  # u_j's permissions are identical to u_i's ones

        for k, v in equal_prms.items():
            if v not in self._users_map:
                self._users_map[v] = [k]
            else:
                self._users_map[v].append(k)

        # reduced user-permission association
        for u in self._users_map:
            self._upa[u] = deepcopy(self._upa_bk[u])

        self._users = set(self._users_map.keys())

    # return the weighed structural complexity of the mined roles and |Roles|, |UA|, and |PA|
    def get_wsc(self):
        nroles = len(self._pa.keys())
        ua_size = sum(map(len, self._ua.values()))
        pa_size = sum(map(len, self._pa.values()))
        return nroles + ua_size + pa_size, nroles, ua_size, pa_size

    def _reduction(self):
        self._copy_pa = deepcopy(self._pa)
        self._copy_ua = deepcopy(self._ua)
        contains = {}  # dictionary (role, set of roles contained in role)
        roles = list(self._pa.items())
        for i in range(0, len(roles) - 1):
            ri = roles[i]
            for j in range(i + 1, len(roles)):
                rj = roles[j]
                if len(ri[1]) < len(rj[1]) and ri[1].issubset(rj[1]):
                    if rj[0] in contains:
                        contains[rj[0]].add(ri[0])
                    else:
                        contains[rj[0]] = {ri[0]}
                if len(rj[1]) < len(ri[1]) and rj[1].issubset(ri[1]):
                    if ri[0] in contains:
                        contains[ri[0]].add(rj[0])
                    else:
                        contains[ri[0]] = {rj[0]}

        for u in self._users:
            for r in self._ua[u]:
                if r in contains:
                    intersection = self._ua[u].intersection(contains[r])
                    self._ua[u] = self._ua[u].difference(intersection)

    # check whether ua and pa cover upa
    def check_solution(self):
        for u in self._users:
            if u not in self._ua.keys():
                return False
            perms = set()
            for r in self._ua[u]:
                perms.update(self._pa[r])

            if perms != self._upa[u]:
                return False
        return True

    def _check_unused_roles(self):
        roles = set()
        for r in self._ua.values():
            roles.update(r)
        if roles != set(self._pa.keys()):
            return True
        else:
            return False

    def __str__(self):
        to_return = '-- dati dataset/esperimento --\n'
        to_return = to_return + self._dataset + '\n'
        to_return = to_return + '#utenti:' + str(len(self._users)) + '\n'
        to_return = to_return + '#permessi:' + str(len(self._permissions)) + '\n'
        to_return = to_return + '|upa|=' + str(self._n) + '\n'
        return to_return

    def solution_data(self):
        print('#roles:', len(self._pa.keys()))
        max_num_roles = 0
        min_num_roles = float('inf')

        for (u, roles) in self._ua.items():
            n_roles = len(roles)
            if n_roles > max_num_roles:
                max_num_roles = n_roles
            if n_roles < min_num_roles:
                min_num_roles = n_roles

        print('Minimo numero di ruoli per utente:', min_num_roles)
        print('Massimo numero di ruoli per utente:', max_num_roles)

        nrp = {}
        roles = list(self._pa.values())
        for r in roles:
            for p in r:
                if p in nrp:
                    nrp[p] = nrp[p] + 1
                else:
                    nrp[p] = 1

        print('Minimo numero di ruoli per permesso:', min(nrp.values()))
        print('Massimo numero di ruoli per permesso:', max(nrp.values()))

    # needed only for debug
    def check_duplicates(self):
        print('-- check duplicates --')
        tmp_roles = list(self._pa.values())
        print('#initial roles', len(tmp_roles))
        roles = []
        for r in tmp_roles:
            if r not in roles:
                roles.append(r)
        print('#final roles', len(roles))
        if len(tmp_roles) == len(roles):
            print('No duplicated roles')
        else:
            print('DUPLICATED roles')

    # needed only for debug
    def duplicated_users(self):
        tmp_users = []
        for u in self._upa.values():
            if u not in tmp_users:
                tmp_users.insert(1, u)
            else:
                print(u, 'già presente')
        print(len(self._users), ' ', len(tmp_users))
        if len(tmp_users) != len(self._users):
            return True
        else:
            return False

    def get_dupa(self):
        _dupa = 0
        for u in self._users:
            if u not in self._ua.keys():
                _dupa = _dupa + len(self._upa[u])
            else:
                prms = set()
                for r in self._ua[u]:
                    prms = prms.union(self._pa[r])
                if prms.issubset(self._upa[u]):
                    _dupa = _dupa + len(self._upa[u] - prms)
                else:
                    print('ERROR!!!')
                    exit(0)
        return _dupa

    def verify(self):
        num_perms = 0
        for u in self._ua.keys():
            prms = set()
            for r in self._ua[u]:
                prms = prms.union(self._pa[r])
            num_perms = num_perms + len(prms)
        dupa = self._n - num_perms
        return dupa


class RM(Mining):
    def __init__(self, dataset, access_matrix='upa', minimum='len',  unique=False):
        super().__init__(dataset, unique)

        # added for the minimum selection idf-based
        self._idf_matrix = self._pua if access_matrix == 'upa' else self._unc_pua

        # use the original UPA or the entries left uncovered in UPA
        assert access_matrix.lower() in ('upa', 'uncupa'), 'Access matrix not recognized'
        self._matrix = self._upa if access_matrix == 'upa' else self._unc_upa

        # self._flag = True if access_matrix == 'uncupa' else False

        # select a user considering the number or the sum of the idf values
        # of his/her assigned permissions in _matrix
        assert minimum in ('len', 'idf'), 'minimum selection not recognized'
        if minimum == 'len':
            self._minimum = lambda u: len(self._matrix[u])
            self._min = 'len'
        else:
            self._minimum = lambda u: sum([self._p_IDF[p] for p in self._matrix[u]])
            self._min = 'idf'

        self._compute_idf()

    def _compute_idf(self):
        # a permission with a small idf value is assigned to more users
        # than a permission with a higher idf value
        self._p_IDF = {p: -math.log(len(self._idf_matrix[p]) / len(self._unc_users), 2) for p in self._idf_matrix}

        # A permission with a small idf value is assigned to more users
        # than a permission with a higher idf value. Sorting the permissions
        # in increasing order and considering the first mpr selects the ones
        # assigned to many users

    def _pick_role(self):
        u = min(self._unc_users, key=self._minimum)
        prms = self._unc_upa[u]
        usrs = {u for u in self._unc_users if prms <= self._matrix[u]}
        return usrs, prms

    def mine(self):
        while self._unc_users:
            usrs, prms = self._pick_role()
            self._update_ua_pa(usrs, prms)
            self._update_unc(usrs, prms)
            if self._matrix is self._unc_upa and self._min == 'idf':
                self._compute_idf()


