import rm
import copy
import random


# return True if  role satisfies the family of constraints
def satisfy(role, constraints):
    for c in constraints:
         if c <= role:
                return False
    return True


class POST_SSP(rm.Mining):
    def __init__(self, ua, pa, cp, modality=1):
        self._modality = modality
        self._users = set(ua.keys())
        self._ua = copy.deepcopy(ua)
        self._pa = copy.deepcopy(pa)
        self._cp = {pos:c for pos, c in enumerate(cp, start=1)}
        self._upa = self._build_upa()


    # construct upa assignments starting from ua and pa assignments
    def _build_upa(self):
        upa = dict()
        for u, roles in self._ua.items():
            upa[u] = set()
            for r in roles:
                upa[u].update(self._pa[r])

        return upa


    def _violating_roles(self):
        violating = dict()

        for role, permissions in self._pa.items():
            violating[role] = [c for c in self._cp.values() if c <= permissions]

        roles = list(violating.keys())
        for role in roles:
            if not violating[role]:
                del violating[role]

        return violating


    # return True if (ua, pa) is a decomposition of upa such that pa satisfies cp
    def check_solution(self):
        if not super().check_solution():
            return False

        for c in self._cp.values():
            for role in self._pa.values():
                if c <= role:
                    return False

        return True


    def mine(self):
        violations = self._violating_roles()
        if not violations:
            return False  # (ua, pa) satisfies the constraints

        #print('\tviolations:', violations)
        if self._modality == 1:
            for role, constraints in violations.items():
                new_role1 = {random.sample(list(c), 1)[0] for c in constraints}
                new_role2 = self._pa[role] - new_role1
                #print('\trole:',  self._pa[role])
                #print('\t  r1:', new_role1)
                #print('\t  r2:', new_role2)

                idx_r1 = idx_r2 = -1
                for idx_role, permissions in self._pa.items():
                    if new_role1 == permissions:
                        idx_r1 = idx_role
                    elif new_role2 == permissions:
                        idx_r2 = idx_role

                #print('\tidx_r1:', idx_r1)
                #print('\tidx_r2:', idx_r2)

                # update pa
                if idx_r1 == -1 and idx_r2 == -1: # two new roles
                    i1 = role
                    i2 = max(self._pa.keys()) + 1
                    self._pa[i1] = copy.deepcopy(new_role1)
                    self._pa[i2] = copy.deepcopy(new_role2)
                elif idx_r1 == -1:
                    i1 = role
                    i2 = idx_r2
                    self._pa[i1] = copy.deepcopy(new_role1)
                elif idx_r2 == -1:
                    i1 = role
                    i2 = idx_r1
                    self._pa[i1] = copy.deepcopy(new_role2)
                else:
                    i1 = idx_r1
                    i2 = idx_r2
                    del self._pa[role]

                # update ua
                for user in self._ua:
                    if role in self._ua[user]:
                        self._ua[user].remove(role)
                        self._ua[user].update({i1, i2})

        elif self._modality == 2:  # USELESS - RM generates very few roles contained in others
            for role, constraints in violations.items():
                contained = {r for r in self._pa if self._pa[r] < self._pa[role] and satisfy(self._pa[r], constraints)}
            print('modality: 2', contained)

        return True