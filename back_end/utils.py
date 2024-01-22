import math
import string
import numpy as np
import itertools as it

from scipy.stats import rankdata
from collections import Counter

def get_stop_words():
    with open('./static/stopwords.txt', 'r') as f:
        words = f.readlines()
        words = [item.strip() for item in words]
        return words

def get_combined_domain(X1, X2):
    """
    Returns a list of the unique elements in two list-like objects. Note that
    there's a lot of ways to make this function, but given how the rest of the
    rank-turbulence divergence function is structured, it's nice to have this
    self-contained version.

    Parameters
    ----------
    X1, X2 (list or np.ndarray or dict):
        Two list-like objects with domains that need to be joined.

    Returns
    -------
    combined_domain (list):
        List of unique elements in the two inputs.

    """

    combined_domain = list(set(X1) | set(X2))

    return combined_domain


def get_rank_dictionary(X, C):
    """
    Returns a dictionary where the keys are the items being ranked and the
    values are their corresponding ranks, using fractional rankings.

    Parameters
    ----------
    X (list or np.ndarray or dict):
        Either a list of raw data (which will need to be counted and reshaped)
        or a dictionary of {element:counts} or a rank-ordered list of elements.
        See the documentation for rank_turbulence_divergence for more details
        about what types of inputs should be provided.

    C (dict):
        Empty dictionary to be populated by counts, then ranked.

    Returns
    -------
    R (dict):
        dict where the keys are the ranked elements and the values are their
        fractional ranking.

    N (int):
        Number of unique elements in X.

    """

    if type(X) == dict:
        dtype_dict = True
        N = len(X)
        c = X.copy()
    else:
        dtype_dict = False
        N = len(set(list(X)))

    if not dtype_dict:
        if len(np.unique(X)) == len(X):
            m = list(range(len(X)))
            aug = [[v] * (m[len(m) - i - 1] + 1) for i, v in enumerate(X)]
            x = list(it.chain.from_iterable(aug))
            c = dict(Counter(x))

        else:
            c = dict(Counter(X))

    for k, v in c.items():
        C[k] += v

    d = list(C.keys())
    counts = list(C.values())

    # strange step, but scipy's ranking function is reversed
    ranking = len(counts) - rankdata(counts) + 1
    R = dict(zip(d, ranking))

    return R, N


def rank_turbulence_divergence(X1, X2, alpha=1.0, topK=30):
    r"""
    Calculates the rank turbulence divergence between two ordered rankings,
    $R_1$ and $R_2$. This is done via the following equation, with a tunable
    ``inverse temperature'' parameter, alpha.

    $ D_{\alpha}^{R}(R_1||R_2) =
        \dfrac{1}{\mathcal{N}_{1,2;\alpha}}
        \dfrac{\alpha+1}{\alpha}
        \sum_{\tau \in R_{1,2;\alpha}}
            \Big\vert \dfrac{1}{\big[r_{\tau,1}\big]^\alpha} -
            \dfrac{1}{\big[r_{\tau,2}\big]^\alpha} \Big\vert^{1/(\alpha+1)} $

    where The $\mathcal{N}_{1,2,\alpha}$ term refers to a normalization factor
    that forces the rank-turbulence divergence between 0 and 1, as follows:

    $ \mathcal{N}_{1,2;\alpha} =
        \dfrac{\alpha+1}{\alpha}
        \sum_{\tau \in R_1}
        \Big\vert \dfrac{1}{\big[r_{\tau,1}\big]^\alpha} -
        \dfrac{1}{\big[N_1+\frac{1}{2}N_2\big]^\alpha} \Big\vert^{1/(\alpha+1)}
        + \dfrac{\alpha+1}{\alpha} \sum_{\tau \in R_1} \Big\vert
        \dfrac{1}{\big[N_2 + \frac{1}{2}N_1\big]^\alpha} -
        \dfrac{1}{\big[r_{\tau,2}\big]^\alpha} \Big\vert^{1/(\alpha+1)} $

    where $N_1$ and $N_2$ are the sizes of $R_1$ and $R_2$ (i.e. the number)
    of things being ranked.

    Parameters
    ----------
    X1, X2 (list or np.ndarray, or dict):
        Two rank-ordered vectors, that do not need to be of the same domain. It
        admits the following datatypes:

            1) X1 = ['mary','jane','chelea','ann'],
               X2 = ['ann','jane','barb','crystal']

               ...as two already-ranked lists of $\tau$s. In X1, then, 'mary'
               would be in rank position 1.0, 'jane' in 2.0, etc.

            2) X1 = ['mary','mary','mary','mary','mary','mary','jane','jane',
                     'jane','chelsea','chelsea','barb']
               X2 = ['ann','ann','ann','ann','ann','jane','jane','jane',
                     'jane','barb','barb','crystal']

                ...as two "raw" datasets, without pre-counting the number of
                elements in each list. Ultimately, in X1, 'mary' shows up 6
                timees, 'jane' shows up 3 times, 'chelsea' shows up 2 times,
                and 'ann' shows up once. This function transforms this input
                data into a dictionary of counts, then ultimately a dictionary
                of ranks, such that $R_1$ and $R_2$ vectors for this example
                are the same as in the first example.

            3) X1 = {'mary':6, 'jane':3, 'chelsea':2, 'ann':1}
               X2 = {'ann':5, 'jane':4, 'barb':2, 'crystal':1}

               ...as two dictionaries of {tau:count}. This might be useful in
               a setting where you're given, for example, vote counts (i.e.,
               {'Bernie Sanders':4000, 'Joseph Biden':2000, ... etc}).


    alpha (float):
        Tuning parameter, acts like an inverse temperature, such that a higher
        value will ``zoom in'' on the data, making small deviations appear very
        important to the final ranking. alpha ranges from 0 to infinity.

    Returns
    -------
    Q (float):
        The rank turbulence divergence between $R_1$ and $R_2$, a scalar
        value between 0 and 1.

    """

    combined_domain = get_combined_domain(X1, X2)
    C1 = {i: 0 for i in combined_domain}
    C2 = {i: 0 for i in combined_domain}

    # Turn both vectors into dictionaries where the key is $\tau$, the property
    # that's being ranked (popular baby names, sports teams, etc.), and the
    # values are their (fractional) rank. This is gonna be useful when we loop
    # through all $\tau$s in order to calculate the rank turbulence divergence.
    R1, N1 = get_rank_dictionary(X1, C1)
    R2, N2 = get_rank_dictionary(X2, C2)

    # Then we're gonna be using certain terms frequently, so might as well
    # turn those values into their own variables and give them useless names.
    alph_exp = 1 / (alpha+1)

    assert R1.keys() == R2.keys()
    r1tau_exp_negalpha = np.array(list(R1.values()), dtype=np.float32)
    r1tau_exp_negalpha = r1tau_exp_negalpha ** (-alpha)
    r2tau_exp_negalpha = np.array(list(R2.values()), dtype=np.float32)
    r2tau_exp_negalpha = r2tau_exp_negalpha ** (-alpha)
    dQ = np.abs(r1tau_exp_negalpha - r2tau_exp_negalpha)
    dQ = dQ ** (alph_exp)

    dQ = dict(zip(list(R1.keys()), dQ.tolist()))
    dQ = dict(sorted(dQ.items(), key=lambda x:x[1], reverse=True))

    # get hot words
    hot_words1 = []
    hot_value1 = []
    hot_words2 = []
    hot_value2 = []

    # 词云的值
    stopwords = get_stop_words()
    for key, value in dQ.items():
        if key in stopwords or key in string.punctuation:
            continue
        if R1[key] > R2[key]:
            hot_words1.append(key)
            hot_value1.append(value)
        else:
            hot_words2.append(key)
            hot_value2.append(value)

        if len(hot_words1) > topK and len(hot_words2) > topK:
            break
    
    hot_words1 = hot_words1[:topK]
    hot_value1 = hot_value1[:topK]
    hot_words2 = hot_words2[:topK]
    hot_value2 = hot_value2[:topK]
    
    min_value = min(hot_value1)
    hot_value1 = [math.ceil(item/min_value * 10) for item in hot_value1]
    H1 = [{"name": word, "value": value} for word, value in zip(hot_words1, hot_value1)]
    
    min_value = min(hot_value2)
    hot_value2 = [math.ceil(item/min_value * 10) for item in hot_value2]
    H2 = [{"name": word, "value": value} for word, value in zip(hot_words2, hot_value2)]
    
    return H2, H1


def get_dateslist():
    dates_list = []
    year = [str(i) for i in range(2005,2022)]
    month = ['01','02','03','04','05','06','07','08','09','10','11','12']
    day = ['01','02','03','04','05','06','07','08','09']+[str(i) for i in range(10,29)]
    for y in  year:
        if y == '2005':
            day0 = day + ['29','30','31']
            for d in day0:
                dates_list.append(y+'-'+'12'+'-'+d)
        else:
            for m in month:
                if m in ['01','03','05','07','08','10','12']:
                    day0 = day + ['29','30','31']
                    for d in day0:
                        dates_list.append(y+'-'+m+'-'+d)
                elif m in ['04','06','09','11']:
                    day0 = day + ['29','30']
                    for d in day0:
                        dates_list.append(y+'-'+m+'-'+d)
                elif m=='02' and y in ['2008','2012','2016','2020']:
                    day0 = day + ['29']
                    for d in day0:
                        dates_list.append(y+'-'+m+'-'+d)
                else:
                    for d in day:
                        dates_list.append(y+'-'+m+'-'+d)
    return dates_list


def get_date_index(date):
    date_list = get_dateslist()
    date_index = date_list.index(date)

    return date_index
