from time import *
from random import shuffle
import sys


class ScheduleHelper:
    """
    A class to handle scheduling using a backtracking algorithm.
    """
    candidates: list
    candidates_cost: dict
    not_available: list
    columns: int
    per_solution_timeout: int
    global_timeout: int

    _min_cost: int
    _search_order: list

    solutions: list

    def __init__(self, candidates: list, candidates_cost: dict, not_available: list, columns=2,
                 per_solution_timeout=7, global_timeout=30):
        """
        Initialize the ScheduleHelper with the provided parameters.
        """
        self.candidates = candidates
        self.candidates_cost = candidates_cost
        self.not_available = not_available
        self.columns = columns
        self.per_solution_timeout = per_solution_timeout
        self.global_timeout = global_timeout

        # Create helper-structures
        self._min_cost = sys.maxsize
        self._search_order = self.determine_search_order()

        self.solutions = list()

    def start_calculation(self) -> bool:
        """
        Using the given values the function tries to find as many solutions as possible using the
        backtracking-algorithm.
        :return: True, if solutions were found, False otherwise
        """
        start_time = time()

        # Copy candidates list, so it can be changed
        new_candidates = self.candidates[:]
        solution_template = [[None] * self.columns for _ in range(len(self.not_available))]

        # Find a solution. If there are not enough candidates and search fails, use more candidates
        while time() < start_time + self.global_timeout:
            while True:
                shuffle(new_candidates)

                solution = self.find_solution(new_candidates, solution_template[:],
                                              self.determine_next_day(None), 0,
                                              int(time()) + self.per_solution_timeout)

                # If a solution is found, we are done. If not: Increase candidate count
                if solution is not None:
                    break

                new_candidates = new_candidates[:] + self.candidates[:]

            # Only add solution to list, if its cost is better or equal to previous solutions
            cost = self.evaluate_solution(solution)
            if cost <= self._min_cost:
                self.solutions.append((solution, cost))
                self._min_cost = cost

        # Sort solution by cost
        self.solutions = sorted(self.solutions, key=lambda x: x[1])

        return len(self.solutions) > 0

    def find_solution(self, candidates: list, solution: list, current_day: int,
                      current_column: int, timeout: int) -> list or None:
        """
        A recursive function using the backtracking technique to find a possible solution of the scheduling-problem.

        :param candidates: the possible candidates (left) for scheduling as a list.
        :param solution: the previous solution on which the algorithm search forward.
        :param current_day: the current day.
        :param current_column: the current column.
        :param timeout: the time on which the algorithm should cancel the operation (in seconds).
        :return: solution
        """
        # Check, if solution is even possible with the amount of candidates
        if len(candidates) < len(self.not_available):
            return None

        # Check if there is still time left
        if timeout - time() < 0:
            return None

        # If solution was found, return solution
        if current_day == -1 \
                and solution[self.determine_prev_day(current_day)][current_column] is not None:
            return solution

        # Try candidates, if no one available: backtrack
        for index, candidate in enumerate(candidates):
            # Ignore unavailable candidates
            if candidate in self.not_available[current_day]:
                continue

            # Ensure candidate is not in same column multiple times
            if candidate in solution[current_day]:
                continue

            # Copy candidate-list and remove current candidate from it
            new_candidates = candidates[:]
            del new_candidates[index]

            temp = [row[:] for row in solution]
            temp[current_day][current_column] = candidate

            if current_column < (self.columns - 1):
                new_solution = self.find_solution(new_candidates, temp, current_day, current_column + 1, timeout)
            else:
                new_solution = self.find_solution(new_candidates, temp,
                                                  self.determine_next_day(current_day), 0, timeout)

            if new_solution is not None:
                return new_solution

        return None

    def evaluate_solution(self, solution: list) -> int:
        """
        Inspects the given solution for optimality and returns its calculated cost.
        :param solution: the solution to evaluate
        :return: the cost of the given solution
        """
        if solution is None:
            return 0

        cost = 0
        cand_appear = dict()

        # Create helper data structure: Dictionary for with every candidate and its appearances in the days
        for candidate in self.candidates:
            cand_appear[candidate] = []

        # For every appearance in schedule note it in cand_appear
        for day, entry in enumerate(solution):
            for candidate in entry:
                if candidate is None:
                    continue
                cand_appear[candidate].append(day)

        for candidate, appearance in cand_appear.items():
            if candidate is None:
                continue
            # Count the appearance of the same candidate multiple times within the schedule
            if len(appearance) > 1:
                cost += 2 ** len(appearance)

                # Calculate distance between appearances (the smaller, the worse)
                for i, a1 in enumerate(appearance):
                    for j, a2 in enumerate(appearance):
                        if not i == j or not i > j:
                            distance = a2 - a1
                            if distance == 1:
                                cost += 50

            # Add extra cost per person
            if candidate in self.candidates_cost:
                cost += self.candidates_cost[candidate] * len(appearance)

        return cost

    def determine_search_order(self) -> list:
        """
        Determines the optimal search order after the heuristic of "most constrained first" to detect possible
        failures early on.
        :return: the optimal search order as a list of days
        """

        # For every day count the number of unavailable persons
        not_available_count = list()
        for i, unavailable in enumerate(self.not_available):
            not_available_count.append((i, len(unavailable)))

        not_available_count = sorted(not_available_count, key=lambda x: x[1], reverse=True)

        result = []

        for day in not_available_count:
            result.append(day[0])

        return result

    def determine_next_day(self, current_day: int or None) -> int:
        """
        Determines the next day to find a solution for using the optimal search-order.
        :param current_day: the current day
        :return: next day
        """
        # Return first day in search_order
        if current_day is None:
            return self._search_order[0]

        # If current_day == last day to search for, return -1 to signal this
        if self._search_order.index(current_day) == (len(self.not_available) - 1):
            return -1

        return self._search_order[self._search_order.index(current_day) + 1]

    def determine_prev_day(self, current_day: int or None) -> int:
        """
        Determines the previous day using the optimal search-order.
        :param current_day: the current day
        :return: previous day
        """
        # Return first day in search_order
        if current_day is None:
            return self._search_order[0]

        # Return last day in search_order
        if current_day == -1:
            return self._search_order[-1]

        # If current_day already first day in search_order, return -1 to signal this
        if self._search_order[self._search_order.index(current_day) - 1] == self._search_order[-1]:
            return -1

        return self._search_order[self._search_order.index(current_day) - 1]

    def print_solution(self, solution: list) -> None:
        """
        For a given solution, print out a per day summary with columns.
        :param solution: the solution
        :return: None
        """
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(solution):
            response = f"{days[i % 7]}: "
            for col, candidate in enumerate(day):
                if candidate is not None:
                    response += f"Column {col + 1}: {candidate} "
            print(response)


def calculation_finished(s_helper: ScheduleHelper):
    print("Finished! These are the cheapest solutions (of " + str(len(s_helper.solutions)) + "):")
    for i in range(0, 5):
        if not i >= len(s_helper.solutions):
            solution, cost = s_helper.solutions[i]
            print("Nr. " + str(i + 1) + " with cost of " + str(cost))
            s_helper.print_solution(solution)
            print("-" * 10)


# For debug-purposes
if len(sys.argv) >= 2:
    if sys.argv[1] == 'debug':
        print("DEBUG")
        candidates = ["A", "B", "C", "D", "E", "F", "G"]
        not_available = [
            [], ["C"], [], ["F", "B"], [], [], ["C"],  # Week 1
            [], ["F", "B"], [], [], ["C"], [], ["F", "B"], []  # Week 2
        ]

        s_helper = ScheduleHelper(candidates, {}, not_available, 4, 10, 120)

        if s_helper.start_calculation():
            calculation_finished(s_helper)

    exit()

# Command-line usage
if __name__ == "__main__":
    candidates_string = input("Please name the candidates for scheduling (as a comma separated list without spaces): ")
    candidates = list()
    for candidate in candidates_string.split(','):
        candidates.append(candidate)

    candidates_cost_string = input("Are there candidates with additional costs? Please name them like A:Cost,B:Cost ")
    candidates_cost = dict()
    for tpl in candidates_cost_string.split(','):
        candidate, cost = tpl.split(':')
        candidates_cost[candidate] = int(cost)

    weeks = int(input("How many weeks should be scheduled? "))
    days_per_week = 7  # Monday to Sunday

    not_available = list()
    for week in range(weeks):
        for day in range(days_per_week):
            na_string = input(f"For week {week + 1}, day {day + 1} (Monday to Sunday), name the candidates that are not available: ")

            not_available.append(list())
            if na_string.strip():  # If there are any unavailable candidates listed
                for na in na_string.split(','):
                    not_available[week * days_per_week + day].append(na)

    columns = int(input("How many columns per day should be scheduled?"))

    print("\n Now some more technical questions. As a starter it's recommended to just use the default values.")
    per_solution_timeout = int(input("For how long should the program search for a specific solution until it " +
                                     "times out? (Default: 30s) ") or 30)

    global_timeout = int(input("For how long should the program try out different solutions until it shows you the " +
                               "the best found? (Default: 60s) ") or 60)

    print("Alright, we can start now. This may take a while (at least " + str(global_timeout) + "s), so please be " +
          "patient.")

    s_helper = ScheduleHelper(candidates, candidates_cost, not_available, columns, per_solution_timeout, global_timeout)

    if s_helper.start_calculation():
        calculation_finished(s_helper)
