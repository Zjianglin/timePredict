# -*- coding: utf-8 -*-

class LogFootprint(object):
    pass

    def __str__(self):
        retlist = []
        retlist.append("Seen activites: (%s)" % ",".join(map(str, self.activities)))
        retlist.append("Direct followers >: (%s)" % ",".join(map(str , self.directly_follows)))
        retlist.append("Causally dep. events ->: (%s)" % ",".join(map(str , self.causal)))
        retlist.append("Not Causally dep. events ->: (%s)" % ",".join(map(str , self.unrelated)))
        retlist.append("Parallel events ->: (%s)" % ",".join(map(str , self.parallel)))
        return "\n".join(retlist)

class Alpha(object):
    '''
    Process discovery by alpha algorithm.
    '''
    def __init__(self, log):
        self.log = log
        self.footprint = self._build_footprint(self.log)
        self.ti = self._make_Ti_set(self.log)
        self.to = self._make_To_set(self.log)
        self.xl = self._make_Xl_set()
        self.yl = self._make_Yl_set(self.xl)

    def __str__(self):
        retlist = []
        retlist.append("Ti set: (%s)" % ",".join(map(str, self.ti)))
        retlist.append("To set: (%s)" % ",".join(map(str, self.to)))
        retlist.append("Xl set: (%s)" % ",".join(map(str, self.xl)))
        retlist.append("Yl set: (%s)" % ",".join(map(str, self.yl)))
        return "\n".join(retlist)

    def _get_activities(self, log):
        activities = set()
        for trace in log:
            for act in trace:
                activities.add(act)
        return activities

    def _directly_follows(self, log):
        '''Return all pairs of activities in a "directly follows" relation.
           i.e. a > b iff there is a trace {...ab...}
        '''
        df = set()
        for trace in log:
            for i in range(len(trace) - 1):
                df.add((trace[i], trace[i+1]))
        return df

    def _causal_dependencies(self, directly_follows):
        '''Return all pairs of activities in a "causal dependency" relation.
           i.e. a --> b iff. a>b & not(b>a)
        '''
        cd = set()
        for df in directly_follows:
            a, b = df
            if (b, a) not in directly_follows:
                cd.add((a, b))
        return cd

    def _unrelated(self, activities, directly_follows):
        '''Return all pairs of activities in a `unrelated` relation.
           i.e. a # b iff not(a>b) and not(b>a)
        '''
        unrelated = set()
        for a in activities:
            for b in activities:
                if a == b:
                    unrelated.add((a, a))
                elif (((a, b) not in directly_follows) and ((b, a) not in directly_follows)):
                    unrelated.add((a, b))
                    unrelated.add((b, a))
        return unrelated

    def _parallel(self, activities, directly_follows):
        '''Return all pairs of activities in a `parallel` relation.
           i.e. a||b iff. a>b and b>a.
        '''
        parallel = set()
        for a in activities:
            for b in activities:
                if (a, b) in directly_follows and (b, a) in directly_follows:
                    parallel.add((a, b))
                    parallel.add((b, a))
        return parallel

    def _build_footprint(self, log):
        '''Return all activities in log and all pairs of four realions in log
        '''
        fp = LogFootprint()
        fp.activities       = self._get_activities(log)
        fp.directly_follows = self._directly_follows(log)
        fp.causal           = self._causal_dependencies(fp.directly_follows)
        fp.unrelated        = self._unrelated(fp.activities, fp.directly_follows)
        fp.parallel         = self._parallel(fp.activities, fp.directly_follows)
        return fp

    def _make_Ti_set(self, log):
        '''Return all start activities'''
        return set([trace[0] for trace in log])

    def _make_To_set(self, log):
        '''Return all end activities'''
        return set([trace[-1] for trace in log])

    def _check_set(self, A, unrelated):
        for e1 in A:
            for e2 in A:
                if (e1, e2) not in unrelated:
                    return False
        return True

    def _check_outsets(self, A, B, causal):
        for e1 in A:
            for e2 in B:
                if (e1, e2) not in causal:
                    return False
        return True

    def _make_Xl_set(self):
        '''Return Xl.
           XL = {(A,B) | A ⊆ TL ∧ A = ∅ ∧ B ⊆ TL ∧ B = ∅ ∧
                ∀a∈A∀b∈B (a →L b) ∧ ∀a1,a2∈A a1#La2 ∧ ∀b1,b2∈B b1#Lb2}.
           where TL is fp.activities.TL = {t ∈ T | ∃σ∈L t ∈ σ}, L is log.
        '''
        import itertools
        Xl = set()
        subsets = set()
        for i in range(1, len(self.footprint.activities)):
            for s in itertools.combinations(self.footprint.activities, i):
                subsets.add(s)

        for A in subsets:
            reta = self._check_set(A, self.footprint.unrelated)
            for B in subsets:
                retb = self._check_set(B, self.footprint.unrelated)
                if reta and retb and self._check_outsets(A, B, self.footprint.causal):
                    Xl.add((A, B))
        return Xl

    def _make_Yl_set(self, Xl):
        '''Return Yl.
           YL = {(A,B) ∈ XL | ∀(A1,B1)∈XL(A ⊆ A1 ∧ B ⊆ B1) ⇒ (A,B) = (A1,B1)}.
        '''
        Yl = set()
        for t1 in Xl:
            A, B = t1
            flag = True
            for t2 in Xl:
                if set(A).issubset(t2[0]) and set(B).issubset(t2[1]) and (t1 != t2):
                    flag = False
                    break
            if flag:
                Yl.add(t1)
        return Yl


