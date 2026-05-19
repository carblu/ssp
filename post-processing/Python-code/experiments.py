import copy
import itertools

import synthetic
import utils
import rm
import post_ssp

GEN_METHODS = 'upa_rnd', 'upa_small', 'pa_rnd', 'pa_small'
VARIANTS = 'OL', 'OI', 'UL', 'UI'

rwd = dict()
rwd['americas_large'] = 'Americas large'
rwd['americas_small'] = 'Americas small'
rwd['apj'] = 'Apj'
rwd['domino'] =' Domino'
rwd['emea'] = 'Emea'
rwd['fire1'] = 'Firewall 1'
rwd['fire2'] = 'Firewall 2'
rwd['hc'] = 'Healthcare'
#rwd['customer'] = 'Customer'




def experiment_type_s(nr, nu, np, mru, mpr, nc=None):
    all_results = dict()
    for modality in GEN_METHODS:
        print('Generating (ua, pa, cp) Modality:', modality)
        results = synthetic_experiment(nr, nu, np, mru, mpr, nc, cp_gen_mode=modality)
        # print(results)
        all_results[modality] = results
        # print()

    return all_results


def experiment_type_rw(dataset, nc=None):
    all_results = dict()
    folder = 'datasets/optimal_decompositions/'
    suffix = '_exact_cover.txt'
    print('dataset name: ', dataset + suffix)
    datasetName = folder + dataset + suffix

    for modality in GEN_METHODS:
        print('Generating (ua, pa, cp) Modality:', modality)
        results = real_world_experiment(datasetName, nc=nc, cp_gen_mode=modality)
        #print(results)
        all_results[modality] = results
        #print()

    return all_results


def synthetic_experiment(nr, nu, np, mru, mpr, nc=None, cp_gen_mode='upa_rnd'):
    if nc is None:
        nc = nu // 10 if 'upa' in cp_gen_mode else nr // 10

    ua_gen, pa_gen, cp = synthetic.generate_dataset(nr, nu, np, mru, mpr, nc, modality=cp_gen_mode)
    rm_result = apply_rm(ua_gen, pa_gen)
    return apply_pp(rm_result, ua_gen, pa_gen, cp)


def real_world_experiment(dataset, nc=None, cp_gen_mode='upa_rnd'):
    ua_orig, pa_orig = utils.load_ua_pa(dataset)

    if nc is None:
        nc = len(ua_orig)//10 if 'upa' in cp_gen_mode else len(pa_orig)//10

    if cp_gen_mode == 'upa_rnd':
        upa = utils.build_upa(ua_orig, pa_orig)
        cp = synthetic.generate_cp(upa, nc, 'random')
    elif cp_gen_mode == 'upa_small':
        upa = utils.build_upa(ua_orig, pa_orig)
        cp = synthetic.generate_cp(upa, nc, 'smallest')
    elif cp_gen_mode == 'pa_rnd':
        cp = synthetic.generate_cp(pa_orig, nc, 'random')
    elif cp_gen_mode == 'pa_small':
        cp = synthetic.generate_cp(pa_orig, nc, 'smallest')
    else:
        raise ValueError('Unknown cp generation mode')

    rm_result = apply_rm(ua_orig, pa_orig)
    return apply_pp(rm_result, ua_orig, pa_orig, cp)


# from (ua_gen, pa_orig) compute upa
# run RM on upa using variants OL, OI, UL, and UI
# return rm_result containing execution results
def apply_rm(ua_gen, pa_gen):
    nr_roles = len(pa_gen)
    wsc = utils.wsc(ua_gen, pa_gen)

    # compute UPA associated to the configuration (UA, PA)
    upa = utils.build_upa(ua_gen, pa_gen)

    # setup test-bed
    h_name = dict()
    upa_c = dict()
    for pos, mode in enumerate(itertools.product(('upa', 'uncupa'), ('len', 'idf'))):
        h_name[mode[0] + mode[1]] = VARIANTS[pos]
        upa_c[mode[0] + mode[1]] = copy.deepcopy(upa)

    rm_result = dict()
    rm_result['base'] = nr_roles, wsc
    rm_result['upa'] = upa

    for matrix, minimum in itertools.product(('upa', 'uncupa'), ('len', 'idf')):
        rm_result[h_name[matrix + minimum]] = list()

        # mine roles from upa
        state = rm.RM(upa_c[matrix + minimum], access_matrix=matrix, minimum=minimum)
        state.mine()
        wsc, nr, _, _ = state.get_wsc()
        pa_rm = state.get_pa()  # compute similarity pa_orig vs pa_rm
        similarity = round((utils.compute_sim(pa_gen, pa_rm) + utils.compute_sim(pa_rm, pa_gen)) / 2, 4)
        jaccard, found = utils.jaccard(pa_gen, pa_rm)
        rm_result[h_name[matrix + minimum]].append((state.check_solution(), nr, wsc, similarity, round(jaccard, 4), found))
        rm_result[h_name[matrix + minimum]].append((state.get_ua(), state.get_pa()))

    return rm_result


# run RM on upa contained in rm_result using variants OL, OI, UL, and UI
# apply post-processing heuristics to ua_orig, pa_orig
def apply_pp(rm_result, ua_orig, pa_orig, cp):
    nr_roles = rm_result['base'][0]
    wsc = rm_result['base'][1]
    upa = rm_result['upa']

    # setup test-bed
    h_name = dict()
    upa_c = dict()
    for pos, mode in enumerate(itertools.product(('upa', 'uncupa'), ('len', 'idf'))):
        h_name[mode[0] + mode[1]] = VARIANTS[pos]
        upa_c[mode[0] + mode[1]] = copy.deepcopy(upa)

    results = dict()
    results['base'] = nr_roles, wsc
    for matrix, minimum in itertools.product(('upa', 'uncupa'), ('len', 'idf')):
        variant = h_name[matrix + minimum]
        results[variant] = list()
        results[variant].append(rm_result[variant][0])

        ua_rm = rm_result[variant][1][0]
        pa_rm = rm_result[variant][1][1]

        # apply post-processing method
        post_state = post_ssp.POST_SSP(ua_rm, pa_rm, cp)
        post_state.mine()
        wsc, nr, _, _ = post_state.get_wsc()
        pa_ssp = post_state.get_pa() # compute similarity pa_orig vs pa_ssp
        similarity = round( (utils.compute_sim(pa_orig, pa_ssp) + utils.compute_sim(pa_ssp, pa_orig)) / 2, 4)
        jaccard1, found = utils.jaccard(pa_orig, pa_ssp)
        results[variant].append((post_state.check_solution(), nr, wsc, similarity, round(jaccard1, 4), found))

        # compute similarity pa_rm vs pa_ssp
        pa_rm = rm_result[variant][1][1]
        similarity = round( (utils.compute_sim(pa_rm, pa_ssp) + utils.compute_sim(pa_ssp, pa_rm)) / 2, 4)
        jaccard2, found = utils.jaccard(pa_rm, pa_ssp)
        results[variant].append((0, 0, 0, similarity, round(jaccard2, 4), found))

        #print(results)

    return results


def print_table(all_results, caption, label):
    # output starting decomposition
    print('\\begin{table}[!ht]')
    print('\\centering')
    print('\\begin{tabular}{cccll}')
    print('\\vr & $|\\rRM|$ & \\wsc & \\simil{gm} & \\jac{gm} \\\\[0.05in]', '\n')
    print('\\toprule')

    result = all_results['upa_rnd']
    for variant in VARIANTS:
        print(f'\\{variant.lower()} &', end=' ')
        for i in range(1, 4):
           print(f' {result[variant][0][i]:<6} &', end=' ')
        print(f' {result[variant][0][4]:<6} \\\\')

    print('\\bottomrule')
    print('\\end{tabular}')
    print('\\caption{Starting decomposition -- Dataset:', caption, f'}}\\label{{tab_s:{label}}}')
    print('\\end{table}')

    print('\n\n')
    # output post-processing computation
    print('\\begin{table}[!ht]')
    print('\\centering')
    print('\\begin{tabular}{ccllllll}')
    print('Modality & \\vr & $|\\rRM|$ & \\wsc  &', end=' ')
    print('\\simil{gp} & \\jac{gp} & \\simil{mp} & \\jac{mp}', end=' ')
    print('\\\\[0.05in]', '\n')


    print('\\toprule')
    for gen_method, result in all_results.items():
        print('\\multirow{4}{*}{\\texttt{', gen_method.replace('_', '-'), '}}')
        for variant in VARIANTS:
            pp_orig = result[variant][1]
            pp_mined = result[variant][2]
            print(f' & \\{variant.lower()} &', end=' ')
            for i in range(1,5):
                print(f' {pp_orig[i]:<6} &', end=' ')

            print(f' {pp_mined[3]:<6} & {pp_mined[4]:<6} \\\\ ')

        print()
        if gen_method == GEN_METHODS[-1]:
            print('\\bottomrule')
        else:
            print('\\midrule')

    print('\\end{tabular}')
    print('\\caption{Post-processing decomposition -- Dataset:', caption ,f'}}\\label{{tab:{label}}}')
    print('\\end{table}')


if __name__ == '__main__':
    print('START')

    #"""
    # Experiments with real world datasets
    nc = 5
    suffix = '_1' if nc is not None else '_2'
    for dataset in rwd:
        #if 'fire1' not in dataset:  continue
        print('\\subsection{', rwd[dataset], f' -- nc = {nc} }}')
        all_results = experiment_type_rw(dataset, nc=nc)
        print_table(all_results, rwd[dataset], label=dataset+suffix)
        print()
   # """





    # Experiments with synthetic datasets
    # DATASET FOR EXPERIMENTS
    # NRoles NUsers NPermissions MRolesUsr MPermissionsRole
    # (nr, nu, np, mru, mpr)

    table_1 = [(100, 200, 50, 3, 5),
               (100, 200, 100, 3, 10),
               (100, 200, 200, 3, 20),
               (100, 400, 200, 3, 20)]


    # CCS2006 Table 2
    # constant number of users/roles, varying permissions
    # (nr, nu, np, mru, mpr)
    ccs_t2 = {'d11':(100, 2000,  100, 3,  10),
              'd12':(100, 2000,  500, 3,  50),
              'd13':(100, 2000, 1000, 3, 100),
              'd14':(100, 2000, 2000, 3, 200)
              }

    # CCS2006 Table 3
    # Varying Users: Constant nr and np, varying nu
    # (nr, nu, np, mru, mpr)
    ccs_t3 = {'d21':(200,  500, 1500, 3, 150),
              'd22':(200, 1000, 1500, 3, 150),
              'd23':(200, 3000, 1500, 3, 150),
              'd24':(200, 5000, 1500, 3, 150)
              }

    # CCS2006 Table 4
    # Varying Roles and Users: Constant np
    ccs_t4 = {'d31':( 10,  100, 1500, 3, 150),
              'd32':( 50,  500, 1500, 3, 150),
              'd33':(100, 1000, 1500, 3, 150),
              'd34':(500, 5000, 1500, 3, 150)
              }


    low_density_1 = [(400, 3_500, 10_000, 4, 40),
                     (400, 4_500, 12_000, 5, 40),
                     (400, 5_500, 14_000, 6, 40),
                     (400, 7_500, 16_000, 7, 40)
                     ]

    #nr, nu, np, mru, mpr = 200, 500, 1500, 3, 150
    # nr, nu, np, mru, mpr = 100, 2000, 500, 3, 50
    # nr, nu, np, mru, mpr = 200, 500, 1500, 3, 150

    """
    nc = None

    for label, data in ccs_t4.items():
        all_results = experiment_type_s(*data, nc)

        print('\\clearpage')
        if nc is None:
            nc = '10\\%'

        suffix = '_1' if nc is not None else '_2'
        caption = '\\texttt{' + label + '}'
        print('\\subsubsection{Dataset', caption, f' -- nc = {nc} }}')
        print_table(all_results, caption=caption, label=label+suffix)
        print()
    """

    print('END')
