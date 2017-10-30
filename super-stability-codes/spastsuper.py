from readinputSPAST import READSPAST
from copy import deepcopy
from time import *


class SPASTSUPER:
    def __init__(self, input):

        self.filename = input
        r = READSPAST()
        r.read_file(self.filename)

        self.students = r.students
        self.projects = r.projects
        self.lecturers = r.lecturers

        self.sp = r.sp
        self.sp_copy = r.sp_copy
        self.sp_no_tie = r.sp_no_tie
        self.sp_no_tie_deletions = r.sp_no_tie_deletions
        self.plc = r.plc
        self.lp = r.lp
        self.lp_copy = r.lp_copy

        self.M = {}
        self.not_assigned = 0
        self.assigned = 0
        self.multiple_assignment = False
        self.lecturer_capacity_checker = False  # if a lecturer's capacity was full during some iteration and subsequently became under-subscribed
        self.project_capacity_checker = False
        self.full_projects = set()

        self.run_algorithm = True
        self.blockingpair = False

        self.time_taken = 0

    def algorithm(self):
        start_time = time()
        # -------------------------------------------------------------------------------------------------------------------
        self.M = {'s' + str(i): set() for i in range(1, self.students+1)}  # assign all students to be free
        unassigned = ['s'+str(i) for i in range(1, self.students+1)]  # keep track of unassigned students
        #unassigned = u[::-1]
        #print(unassigned)
        # ------------------------------------------------------------------------------------------------------------------------
        #  -------------------------------------------------ALGORITHM STARTS HERE -------------------------------------------------
        # ------------------------------------------------------------------------------------------------------------------------
        count_running = 1  # debugging purpose, to know the number of times the while loop is repeated..
        while self.run_algorithm is True:
            self.run_algorithm = False
            while unassigned:  # while some student is unassigned
                student = unassigned.pop(0)  # the student at the tail of the list ::: super-stable matching is the same irrespective of which student is chosen first
                #print(student)
                s_preference = self.sp[student][1]  # the projected preference list for this student.. this changes during the allocation process.

                # if student_progress is not up to student length --- length is not 0-based!
                if self.sp[student][3] < self.sp[student][0]:  # if the preference list counter has not been exceeded
                    # store the projects at the head of the list in the variable tie, could be length 1 or more
                    tie = s_preference[self.sp[student][3]]
                    self.sp[student][3] += 1  # move the pointer to the next tie on the student's ordered preference list

                    for first_project in tie:
                        if first_project == 'dp':
                            continue
                        else:
                            lecturer = self.plc[first_project][0]
                            self.M[student].add(first_project)  # provisionally assign the first_project to student
                            self.plc[first_project][1] -= 1  # reduce the capacity of first_project
                            self.lp[lecturer][0] -= 1  # reduce the capacity of lecturer
                            ##################################################################################################################
                            #  ------------------------------------- IF PROJECT IS OVERSUBSCRIBED --------------------------------------------
                            ##################################################################################################################
                            if self.plc[first_project][1] < 0:  # project is oversubscribed
                                # ----- get the (TAIL) tie of the worst student assigned to this project according to the lecturer offering it----
                                fp_students = self.lp[lecturer][2][first_project]  # students who chose p_j according to Lk -
                                # -------- next we delete first_project on the preference list of students contained in the tail of L_k_j --------
                                # what we do is replace first_project with a dummy project dp, to avoid the complexity of .remove from the list.
                                index = self.plc[first_project][5]  # stores the position of the tail in L_k_j
                                tail = fp_students[index]
                                for worst_student in tail:
                                    try:
                                        # get the rank of pj on the student's list
                                        # say (2, 0) :::: 2 is position of the tie containing first_project on student's ordered preference list
                                        # while 0 is the position of first_project in the tie
                                        p_rank = self.sp[worst_student][2][first_project]
                                        self.sp[worst_student][1][p_rank[0]][p_rank[1]] = 'dp'  # we replace the project in this position by a dummy project
                                        self.sp_no_tie_deletions[worst_student].remove(first_project)  # removing from a set is O(1)
                                        self.plc[first_project][3] = set()  # this is to make sure that only the best student (any if more than 1) rejected from a project is captured
                                        self.plc[first_project][3].add(worst_student)  # keep track of students who were rejected from first_project
                                    except:
                                        pass
                                    # ---- if the student is provisionally assigned to that project, we break the assignment..
                                    if first_project in self.M[worst_student]:
                                        self.M[worst_student].remove(first_project)  # data structure in use is set to make remove fast..
                                        self.plc[first_project][1] += 1  # increment the project capacity
                                        self.lp[lecturer][0] += 1  # increment the lecturer capacity
                                    # ---- note that if worst_student no longer has any provisional projects, and non-empty preference list
                                    # we add them back to the unassigned list..
                                    if worst_student != student and worst_student not in set(unassigned) and self.M[worst_student] == set() and len(self.sp_no_tie_deletions[worst_student]) != 0:
                                        unassigned.append(worst_student)

                                # ------- we move the worst student pointer from the tail by decrementing the counter
                                self.plc[first_project][5] -= 1
                            ##############################################################################################################

                            ###############################################################################################################
                            #  ------------------------------------- IF LECTURER IS OVERSUBSCRIBED ---------------------------------------------------
                            ###############################################################################################################
                            elif self.lp[lecturer][0] < 0:  # lecturer is oversubscribed
                                lp_students = self.lp[lecturer][1]  # the lecturer's ordered preference list
                                # ----- get the (TAIL) tie of the worst student assigned to this lecturer according to L_k
                                # ---------- for each student in the tail, delete all the projects they have in common with l_k-------
                                P_k = set([i for i in self.lp[lecturer][2].keys()])  # all the projects that lecturer is offering
                                index = self.lp[lecturer][5]  # stores the position of worst_student in L_k
                                tail = lp_students[index]
                                for worst_student in tail:
                                    A_s = set(self.sp_no_tie_deletions[worst_student])  # the student's altered preference list without ties.. !!** why not self.sp_no_tie_deletions??
                                    common_projects = list(P_k.intersection(A_s))
                                    for project in common_projects:
                                        try:
                                            # get the rank of pj on the student's list
                                            # say (2, 0) :::: 2 is position of the tie containing first_project on student's ordered preference list
                                            # while 0 is the position of first_project in the tie
                                            p_rank = self.sp[worst_student][2][project]
                                            self.sp[worst_student][1][p_rank[0]][p_rank[1]] = 'dp'
                                            self.sp_no_tie_deletions[worst_student].remove(project)
                                            self.plc[project][3] = set()  # this is to make sure that only the best student rejected from a project is captured
                                            self.plc[project][3].add(worst_student)  # keep track of students who were rejected from this project
                                        except:
                                            pass
                                        # ---- if the student is provisionally assigned to that project, we break the assignment..
                                        if project in self.M[worst_student]:
                                            self.M[worst_student].remove(project)  # data structure in use is set to make remove faster..
                                            self.plc[project][1] += 1  # increment the project capacity
                                            self.lp[lecturer][0] += 1  # increment the lecturer capacity
                                    # ---- note that if worst_student no longer has any provisional projects, we add them back to the unassigned list..
                                    # need to be sure worst student is not the current student in the while loop iteration, because if she is added back to the unassigned students
                                    # she could (in this same iteration) end up being assigned a project in the head of her list which she is yet to apply to
                                    if worst_student != student and worst_student not in set(unassigned) and self.M[worst_student] == set() and len(self.sp_no_tie_deletions[worst_student]) != 0:
                                        unassigned.append(worst_student)
                                # ------- we move the worst student pointer from the tail by decrementing the counter
                                        self.lp[lecturer][5] -= 1
                            ##############################################################################################################

                            ###############################################################################################################
                            #  ------------------------------------- IF PROJECT IS FULL ---------------------------------------------------
                            ###############################################################################################################
                            if self.plc[first_project][1] == 0:  # project is full  ---
                                self.plc[first_project][2] = True  # keep track of this
                                # get the pointer for the worst student assigned to this project according to the lecturer offering it.
                                fp_students = self.lp[lecturer][2][first_project]  # students who chose p_j according to Lk -
                                found = False
                                while found is False:   # exit the loop as soon as a worst student assigned to p_j is found
                                    worst_student_tie = fp_students[self.plc[first_project][5]]  # students who chose p_j according to Lk -
                                    for find_worst_student in worst_student_tie:
                                        if first_project in self.M[find_worst_student]:
                                            found = True
                                            #worst_student = find_worst_student
                                            break   # exit the for loop as soon as a worst student assigned to p_j is found
                                    # if no worst assigned student is found, we decrement the project worst counter and repeat the process again..
                                    if found is False:
                                        self.plc[first_project][5] -= 1

                                #  next we delete p_j on the preference of students who comes after find_worst_student on p_j's according to L_k
                                # what we do is replace p_j with a dummy project dp
                                index = self.plc[first_project][5]+1  # shift the counter to the strict successors of worst_student
                                while index < self.plc[first_project][4]:  # if that position is exactly the length of L_k_j, we are done..
                                    strict_successor_tie = fp_students[index]
                                    for successor in strict_successor_tie:
                                        if first_project in self.sp_no_tie_deletions[successor]:
                                            try:
                                                # get the rank of pj on the student's list
                                                # say (2, 0) - 2 is position of strict_successor_tie in L_k_j. 0 is that of successor in strict_successor_tie
                                                p_rank = self.sp[successor][2][first_project]
                                                self.sp[successor][1][p_rank[0]][p_rank[1]] = 'dp'  # we replace the project in this position by a dummy project
                                                self.sp_no_tie_deletions[successor].remove(first_project)
                                                # self.plc[first_project][3].add(successor)  # keep track of students who were rejected from first_project
                                            except:
                                                pass
                                    index += 1
                            ###############################################################################################################
                            ###############################################################################################################
                            #  ------------------------------------- IF LECTURER IS FULL ---------------------------------------------------
                            ###############################################################################################################
                            if self.lp[lecturer][0] == 0:  # lecturer is full
                                self.lp[lecturer][3] = True  # set the lecturer's capacity checker to True
                                lp_students = self.lp[lecturer][1]  # students who are preferred by
                                P_k = set([i for i in self.lp[lecturer][2].keys()])  # all the projects that lecturer is offering
                                found = False
                                while found is False:  # exit the loop as soon as a worst student assigned to l_k is found
                                    worst_student_tie = lp_students[self.lp[lecturer][5]]  # students who chose projects offered by l_k -
                                    for find_worst_student in worst_student_tie:
                                        # if the student has at least one assigned project offered by lecturer
                                        if any(project in P_k for project in self.M[find_worst_student]):
                                            found = True
                                            break  # exit the for loop as soon as a worst student assigned to p_j is found
                                    # if no worst assigned student is found, we decrement the lecturer's worst counter and repeat the process again..
                                    if found is False:
                                        self.lp[lecturer][5] -= 1

                                index = self.lp[lecturer][5] + 1  # shift the counter to the strict successor of the worst_student in L_k
                                while index < self.lp[lecturer][4]:  # if that position is exactly the length of L_k's list, we are done..
                                    strict_successor_tie = lp_students[index]
                                    for successor in strict_successor_tie:
                                        A_s = set(self.sp_no_tie_deletions[successor])  # the student's altered preference list without ties..
                                        common_projects = list(P_k.intersection(A_s))
                                        for project in common_projects:
                                            try:
                                                p_rank = self.sp[successor][2][project]
                                                self.sp[successor][1][p_rank[0]][p_rank[1]] = 'dp'
                                                self.sp_no_tie_deletions[successor].remove(project)
                                                #  self.plc[project][3].add(successor)  # keep track of students who were rejected from project
                                            except:
                                                pass
                                        # if self.M[successor] == set() and self.sp[successor][3] < self.sp[successor][0] and successor not in unassigned:
                                        #     unassigned.append(student)
                                    index += 1
                            ##############################################################################################################

                #########################################################################################################################################
                # !* remember to move to the end
                # !* if the current student is unassigned in the matching, with a non-empty preference list, we re-add the student to the unassigned list

                # if self.M[student] == set() and len(self.sp_no_tie_deletions[student]) != 0:  --- caught in an infinite while loop for tie-9 (check later!**)
                if self.M[student] == set() and self.sp[student][3] < self.sp[student][0]:
                    unassigned.append(student)
                #########################################################################################################################################

            ###############################################################################################################################################
            # --- At this point, the current execution of the while loop is done and all unassigned students has an empty list..
            # if a project p_j which was previously full is undersubscribed at this point, if s_r is a best student rejected from p_j and the tail of l_k
            # is no better than the tie containung s_r on L_k, we delete each students at the tail of l_k from l_k's preference list
            ###############################################################################################################################################

            for project in self.plc:
                if self.run_algorithm is True:  # breaks out of this loop when some set of deletions sufficient to kick-start the while loop has been done
                    break
                if self.plc[project][1] > 0 and self.plc[project][2] is True:
                    lecturer = self.plc[project][0]
                    P_k = set([i for i in self.lp[lecturer][2].keys()])  # all the projects that lecturer is offering
                    position_worst_tie = self.lp[lecturer][5]  # the last tie on L_k that is yet to be deleted from l_k's preference list
                    Q = self.lp[lecturer][1][position_worst_tie][:]  # deep copy of the tail of L_k
                    # some or all of the students in Q might not be assigned to l_k in M -- some of them might even be better than the rejected_students
                    # we need to check if the students in Q are no better than the best student rejected from p_j, according to L_k
                    if len(Q) > 0:
                        best_student_rejected = self.plc[project][3].pop()
                        self.plc[project][3].add(best_student_rejected)  # I popped and added the student back because set does not support indexing/slicing
                        # the following while loop is checking to see if l_k prefers best_students_rejected and the students in Q, or is indifferent between them
                        # how about we check all the students inward from position_worst_tie, then we stop when this best_student_rejected (s_r) is found
                        while (position_worst_tie) >= 0:  # check all the ties of/before the students in Q to see if it contains best_student_rejected
                            if best_student_rejected in self.lp[lecturer][1][position_worst_tie]:
                                self.run_algorithm = True
                                break
                            position_worst_tie -= 1

                        if self.run_algorithm is True:
                            for s_t in Q:
                                A_t = set(self.sp_no_tie_deletions[s_t])  # the student's altered preference list without ties..
                                common_projects = list(P_k.intersection(A_t))
                                for p_u in common_projects:
                                    try:
                                        p_rank = self.sp[s_t][2][p_u]
                                        self.sp[s_t][1][p_rank[0]][p_rank[1]] = 'dp'
                                        self.sp_no_tie_deletions[s_t].remove(p_u)
                                        self.plc[p_u][3] = set()
                                        self.plc[p_u][3].add(s_t)
                                    except:
                                        pass
                                    # ---- if the student is provisionally assigned to that project, we break the assignment..
                                    if p_u in self.M[s_t]:
                                        self.M[s_t].remove(p_u)  # data structure in use is set to make remove faster..
                                        self.plc[p_u][1] += 1  # increment the project capacity
                                        self.lp[lecturer][0] += 1  # increment the lecturer capacity
                                # ---- if the worst_student no longer has any provisional projects, but has a non-empty preference list
                                #  we add them back to the unassigned list..
                                if self.M[s_t] == set() and len(self.sp_no_tie_deletions[s_t]) > 0:
                                    unassigned.append(s_t)

                            self.lp[lecturer][5] -= 1  # the position of lecturer's worst tie moves inward by the number of ties deleted (which is 1)

        #####################################################################################################################################################
        # If our final assignment relation has any of these three conditions, we can safely report that no super-stable matching exists in the given instance
        #####################################################################################################################################################
        self.time_taken = time() - start_time
        # -------------------------------------------------------------------------------------------------------------------------------
        #   --------------------- 1 ::::  A STUDENT IS MULTIPLY ASSIGNED  -----------------------------
        # -------------------------------------------------------------------------------------------------------------------------------
        for student in self.M:
            if len(self.M[student]) > 1:
                # print(student + ' is assigned to ' + str(len(self.M[student])) + ' projects.')
                self.multiple_assignment = True
                break

        # -------------------------------------------------------------------------------------------------------------------------------
        #   --------------------- 2 :::: A LECTURER WAS FULL at some point and subsequently ends up UNDER-SUBSCRIBED --------------
        # -------------------------------------------------------------------------------------------------------------------------------
        if self.multiple_assignment is False:
            for lecturer in self.lp:
                if self.lp[lecturer][0] > 0 and self.lp[lecturer][3] is True:  # lecturer's capacity is under-subscribed but was previously full
                    self.lecturer_capacity_checker = True
                    P_k = [i for i in self.lp[lecturer][2].keys()]  # all the projects that lecturer is offering
                    for project in P_k:
                        if self.plc[project][1] > 0 and self.plc[project][2] is True:
                            self.project_capacity_checker = True
                            break
                    break

        # -------------------------------------------------------------------------------------------------------------------------------
        #   ----------- 3 :::: A PROJECT WAS REJECTED FROM A STUDENT at some point and subsequently p_j, l_k ends up UNDER-SUBSCRIBED --
        # -------------------------------------------------------------------------------------------------------------------------------
        if self.multiple_assignment is False and self.lecturer_capacity_checker is False:
            for project in self.plc:
                lecturer = self.plc[project][0]
                if len(self.plc[project][3]) > 0 and self.lp[lecturer][0] > 0 and self.plc[project][1] > 0:
                    self.project_capacity_checker = True
                    break

############################################################################################################################################
############################################################################################################################################

    ############################################################################################################################################
    #  ---- If the three conditions above does not halt the algorithm, verify the matching is super-stable by making sure no (student, project)
    #  pair blocks the assignment relation...
    ############################################################################################################################################
    #  -------------------------------------------------------------------------------------------------------------------------------
    #   --------------------- BLOCKING PAIR CRITERIA ----------------------
    # -------------------------------------------------------------------------------------------------------------------------------
    def blockingpair1(self, project, lecturer):
        #  project and lecturer are both under-subscribed
        if self.plc[project][1] > 0 and self.lp[lecturer][0] > 0:
            self.blockingpair = True

    def blockingpair2a(self, student, project, lecturer, matched_project):
        #  project is under-subscribed, lecturer is full and s_i is in M(l_k)
        #  that is, student is matched to a project offered by l_k
        if self.plc[project][1] > 0 and self.lp[lecturer][0] == 0 and self.plc[matched_project][0] == lecturer:
            self.blockingpair = True

    def blockingpair2b(self, student, project, lecturer):
        #  project is under-subscribed, lecturer is full and l_k strictly prefers s_i to its worst student in M(l_k) or is indifferent between them
        if self.plc[project][1] > 0 and self.lp[lecturer][0] == 0:
            # check if s_i's tie is in a position with/before l_k's worst assigned student's tie
            position_worst_tie = self.lp[lecturer][5]
            while position_worst_tie >= 0:  # check all the ties of/before the worst assigned tie to see if student is contained there
                if student in self.lp[lecturer][1][position_worst_tie]:
                    self.blockingpair = True
                    break  # breaks out of the while loop as soon as that student is found!
                position_worst_tie -= 1

    def blockingpair3(self, student, project, lecturer):
        #  project is full and lecturer prefers s_i to the worst student assigned to M(p_j) or is indifferent between them
        if self.plc[project][1] == 0:
            position_worst_tie = self.plc[project][5]
            while position_worst_tie >= 0:  # check all the ties of/before the worst assigned tie to see if student is contained there
                if student in self.lp[lecturer][2][project][position_worst_tie]:
                    self.blockingpair = True
                    break  # breaks out of the while loop as soon as that student is found!
                position_worst_tie -= 1
    # -------------------------------------------------------------------------------------------------------------------------------
    #   ----------------- FIND BLOCKING PAIR ---------- If one exist, self.blockingpair is set to True and this bit halts .. ---
    # -------------------------------------------------------------------------------------------------------------------------------

    def check_stability(self):
        for student in self.M:
            if self.M[student] == set():  # if student s_i is not assigned in M, we check if it forms a blocking pair with all the projects in A(s_i).
                self.not_assigned += 1
                preferred_projects = self.sp_no_tie[student]  # list of pj's wrt to s_i s6 = ['p2', 'p3', 'p4', 'p5', 'p6']

            else:  # if student s_i is matched to a project in M
                self.assigned += 1
                matched_project = self.M[student].pop()  # get the matched project
                self.M[student].add(matched_project)
                rank_matched_project = self.sp_copy[student][2][matched_project]  # find its rank on s_i's preference list A(s_i)
                p_list = self.sp_copy[student][1]  # list of pj's wrt to s_i      # a copy of A(s_i)
                temp = rank_matched_project[0]  # position of the tie of the matched project in the list
                preferred_projects = set()  # projects that student strictly prefers to her matched project or indifferent between..
                while temp >= 0:
                    keep = set([p for p in p_list[temp] if p is not matched_project])
                    preferred_projects.update(keep)
                    temp -= 1

            for project in preferred_projects:
                lecturer = self.plc[project][0]  # l_k

                self.blockingpair1(project, lecturer)  # project and lecturer is under-subscribed
                if self.blockingpair is True:
                    break

                if self.M[student] != set():  # this is the only blocking pair difference between a matched and unmatched student..
                    matched_project = self.M[student].pop()  # get the matched project
                    self.M[student].add(matched_project)
                    self.blockingpair2a(student, project, lecturer, matched_project)  # project is under-subscribed lecturer is full
                    if self.blockingpair is True:
                        break

                self.blockingpair2b(student, project, lecturer)  # project is under-subscribed lecturer is full
                if self.blockingpair is True:
                    break

                self.blockingpair3(student, project, lecturer)
                if self.blockingpair is True:
                    break

            if self.blockingpair is True:
                break