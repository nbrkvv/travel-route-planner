"""Behavioral checks of the domain contract; python -m unittest -v."""
import unittest
from dataclasses import replace
from decimal import Decimal

from demo import example
from planner import (NearestNextStrategy, NoFeasibleRoute, PreferenceFirstStrategy,
                     RouteConstraints, RoutePlanner, TravelMatrix)


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.items, self.prefs, self.matrix = example()
        self.planner = RoutePlanner(NearestNextStrategy())

    def test_switch_strategy_same_context(self) -> None:
        first = self.planner.plan(self.items, self.prefs, self.matrix)
        self.planner.set_strategy(PreferenceFirstStrategy())
        second = self.planner.plan(self.items, self.prefs, self.matrix)
        self.assertEqual([s.place.id for s in first.stops], ['A', 'C'])
        self.assertEqual([s.place.id for s in second.stops], ['B', 'C'])
        self.assertEqual((first.finish_minute, second.finish_minute), (650, 685))

    def test_empty_and_short_window(self) -> None:
        for items, prefs in [([], self.prefs), (self.items, replace(self.prefs, end_minute=550))]:
            with self.assertRaises(NoFeasibleRoute):
                self.planner.plan(items, prefs, self.matrix)

    def test_exact_time_and_budget(self) -> None:
        plan = self.planner.plan([self.items[1]], replace(self.prefs, end_minute=640, budget=Decimal('500')), self.matrix)
        self.assertEqual(plan.finish_minute, 640)
        with self.assertRaises(NoFeasibleRoute):
            self.planner.plan([self.items[1]], replace(self.prefs, budget=Decimal('499')), self.matrix)

    def test_wait_for_opening(self) -> None:
        item = replace(self.items[0], place=replace(self.items[0].place, opens=560))
        stop = self.planner.plan([item], self.prefs, self.matrix).stops[0]
        self.assertEqual((stop.arrival, stop.visit_start, stop.departure), (545, 560, 600))

    def test_unknown_cost_and_hours(self) -> None:
        for place in [replace(self.items[0].place, cost=None), replace(self.items[0].place, opens=None, closes=None)]:
            with self.assertRaises(NoFeasibleRoute):
                self.planner.plan([replace(self.items[0], place=place)], self.prefs, self.matrix)

    def test_closed_place(self) -> None:
        item = replace(self.items[0], place=replace(self.items[0].place, closes=570))
        with self.assertRaises(NoFeasibleRoute):
            self.planner.plan([item], self.prefs, self.matrix)

    def test_directed_and_missing_edges(self) -> None:
        matrix = TravelMatrix({('S', 'A'): 5})
        self.assertIsNone(matrix.duration('A', 'S'))
        with self.assertRaises(NoFeasibleRoute):
            self.planner.plan([self.items[0]], self.prefs, matrix)

    def test_required_place_priority(self) -> None:
        plan = self.planner.plan(self.items, replace(self.prefs, required_ids=frozenset({'B'})), self.matrix)
        self.assertEqual(plan.stops[0].place.id, 'B')

    def test_missing_or_infeasible_required(self) -> None:
        for required in ['X', 'B']:
            with self.assertRaises(NoFeasibleRoute):
                self.planner.plan(self.items, replace(self.prefs, required_ids=frozenset({required}), budget=Decimal('0')), self.matrix)

    def test_invalid_inputs(self) -> None:
        for prefs in [replace(self.prefs, budget=Decimal('-1')), replace(self.prefs, end_minute=500)]:
            with self.assertRaises(ValueError):
                self.planner.plan(self.items, prefs, self.matrix)
        with self.assertRaises(ValueError):
            self.planner.plan(self.items * 2, self.prefs, self.matrix)
        with self.assertRaises(ValueError):
            self.planner.plan(self.items, self.prefs, TravelMatrix({('S', 'A'): -1}))

    def test_deterministic_ties(self) -> None:
        items = [replace(item, score=0.5) for item in reversed(self.items)]
        self.planner.set_strategy(PreferenceFirstStrategy())
        self.assertEqual(self.planner.plan(items, self.prefs, self.matrix).stops[0].place.id, 'A')

    def test_final_validation_rejects_corrupted_result(self) -> None:
        plan = self.planner.plan(self.items, self.prefs, self.matrix)
        with self.assertRaises(NoFeasibleRoute):
            RouteConstraints().verify(replace(plan, total_cost=Decimal('1')), self.items, self.prefs, self.matrix)


if __name__ == '__main__':
    unittest.main()
