"""Pure domain prototype of the Route Planner component. Python 3.10+."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from typing import Mapping, Protocol, Sequence


class NoFeasibleRoute(ValueError):
    """No nonempty feasible plan was found by this heuristic."""


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    visit_minutes: int
    cost: Decimal | None
    opens: int | None
    closes: int | None


@dataclass(frozen=True)
class RankedPlace:
    place: Place
    score: float


@dataclass(frozen=True)
class TripPreferences:
    start_id: str
    end_id: str
    start_minute: int
    end_minute: int
    budget: Decimal
    required_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class TravelMatrix:
    """Directed snapshot. Missing/None edge means unreachable; minutes."""
    minutes: Mapping[tuple[str, str], int | None]

    def duration(self, source: str, target: str) -> int | None:
        if source == target:
            return 0
        return self.minutes.get((source, target))


@dataclass(frozen=True)
class RouteStop:
    place: Place
    arrival: int
    visit_start: int
    departure: int


@dataclass(frozen=True)
class RoutePlan:
    stops: tuple[RouteStop, ...]
    finish_minute: int
    total_cost: Decimal
    total_score: float


class RoutePlanningStrategy(Protocol):
    def order(self, candidates: Sequence[RankedPlace], current_id: str,
              matrix: TravelMatrix) -> list[RankedPlace]:
        """Return every candidate exactly once in the preferred order."""
        ...


class NearestNextStrategy:
    def order(self, candidates: Sequence[RankedPlace], current_id: str,
              matrix: TravelMatrix) -> list[RankedPlace]:
        def key(item: RankedPlace) -> tuple[float, str]:
            duration = matrix.duration(current_id, item.place.id)
            return (float('inf') if duration is None else duration, item.place.id)
        return sorted(candidates, key=key)


class PreferenceFirstStrategy:
    def order(self, candidates: Sequence[RankedPlace], current_id: str,
              matrix: TravelMatrix) -> list[RankedPlace]:
        return sorted(candidates, key=lambda item: (-item.score, item.place.id))


class RouteConstraints:
    """Shared hard constraints, independent of the choice of strategy."""

    def validate(self, candidates: Sequence[RankedPlace], preferences: TripPreferences,
                 matrix: TravelMatrix) -> None:
        if not (0 <= preferences.start_minute < preferences.end_minute <= 1440):
            raise ValueError('Invalid single-day time window')
        if not preferences.budget.is_finite() or preferences.budget < 0:
            raise ValueError('Budget must be finite and nonnegative')
        ids = [item.place.id for item in candidates]
        if len(ids) != len(set(ids)) or any(not id_ for id_ in ids):
            raise ValueError('Candidate IDs must be unique and nonempty')
        if {preferences.start_id, preferences.end_id} & set(ids):
            raise ValueError('Start/end IDs must be distinct from place IDs')
        if not preferences.start_id or not preferences.end_id:
            raise ValueError('Start/end IDs must be nonempty')
        if not preferences.required_ids <= set(ids):
            raise NoFeasibleRoute('Required place is missing from candidates')
        for item in candidates:
            place = item.place
            if not isfinite(item.score) or not 0 <= item.score <= 1:
                raise ValueError('Score must lie in [0, 1]')
            if place.visit_minutes <= 0:
                raise ValueError('Visit duration must be positive')
            if place.cost is not None and (not place.cost.is_finite() or place.cost < 0):
                raise ValueError('Cost must be finite and nonnegative')
            if (place.opens is None) != (place.closes is None):
                raise ValueError('Both opening bounds must be known or unknown')
            if place.opens is not None and place.closes is not None:
                if not 0 <= place.opens < place.closes <= 1440:
                    raise ValueError('Invalid opening interval')
        for duration in matrix.minutes.values():
            if duration is not None and (type(duration) is not int or duration < 0):
                raise ValueError('Travel durations must be nonnegative integers')

    def extend(self, item: RankedPlace, current_id: str, now: int,
               spent: Decimal, preferences: TripPreferences,
               matrix: TravelMatrix) -> RouteStop | None:
        place = item.place
        travel = matrix.duration(current_id, place.id)
        back = matrix.duration(place.id, preferences.end_id)
        if (travel is None or back is None or place.cost is None
                or place.opens is None or place.closes is None):
            return None
        arrival = now + travel
        visit_start = max(arrival, place.opens)
        departure = visit_start + place.visit_minutes
        if (departure > place.closes or departure + back > preferences.end_minute
                or spent + place.cost > preferences.budget):
            return None
        return RouteStop(place, arrival, visit_start, departure)

    def verify(self, plan: RoutePlan, candidates: Sequence[RankedPlace],
               preferences: TripPreferences, matrix: TravelMatrix) -> None:
        by_id = {item.place.id: item for item in candidates}
        now, current, spent = preferences.start_minute, preferences.start_id, Decimal('0')
        seen: set[str] = set()
        score = 0.0
        for stop in plan.stops:
            if stop.place.id not in by_id or stop.place.id in seen:
                raise NoFeasibleRoute('Invalid or repeated stop')
            item = by_id[stop.place.id]
            expected = self.extend(item, current, now, spent, preferences, matrix)
            if expected != stop or expected is None:
                raise NoFeasibleRoute('Route failed final validation')
            seen.add(stop.place.id)
            now, current = stop.departure, stop.place.id
            assert stop.place.cost is not None
            spent += stop.place.cost
            score += item.score
        back = matrix.duration(current, preferences.end_id)
        if not seen:
            raise NoFeasibleRoute('No nonempty route found within the constraints')
        if not preferences.required_ids <= seen:
            raise NoFeasibleRoute('Not all required places could be included')
        if (back is None
                or now + back > preferences.end_minute
                or plan.finish_minute != now + back or plan.total_cost != spent
                or abs(plan.total_score - score) > 1e-9):
            raise NoFeasibleRoute('Route failed final validation')


class RoutePlanner:
    def __init__(self, strategy: RoutePlanningStrategy,
                 constraints: RouteConstraints | None = None) -> None:
        self._strategy = strategy
        self._constraints = constraints if constraints is not None else RouteConstraints()

    def set_strategy(self, strategy: RoutePlanningStrategy) -> None:
        self._strategy = strategy

    def plan(self, candidates: Sequence[RankedPlace], preferences: TripPreferences,
             matrix: TravelMatrix) -> RoutePlan:
        self._constraints.validate(candidates, preferences, matrix)
        remaining = list(candidates)
        stops: list[RouteStop] = []
        current, now = preferences.start_id, preferences.start_minute
        spent, score = Decimal('0'), 0.0
        while remaining:
            required = [item for item in remaining if item.place.id in preferences.required_ids]
            pool = required if required else remaining
            ordered = self._strategy.order(pool, current, matrix)
            pool_by_id = {item.place.id: item for item in pool}
            if sorted(item.place.id for item in ordered) != sorted(item.place.id for item in pool):
                raise ValueError('Strategy must return every candidate exactly once')
            if any(item != pool_by_id[item.place.id] for item in ordered):
                raise ValueError('Strategy must preserve candidate data')
            choice: tuple[RankedPlace, RouteStop] | None = None
            for item in ordered:
                stop = self._constraints.extend(item, current, now, spent, preferences, matrix)
                if stop is not None:
                    choice = item, stop
                    break
            if choice is None:
                break
            item, stop = choice
            stops.append(stop)
            assert item.place.cost is not None
            spent += item.place.cost
            score += item.score
            current, now = item.place.id, stop.departure
            remaining.remove(item)
        back = matrix.duration(current, preferences.end_id)
        if back is None:
            raise NoFeasibleRoute('Final destination is unreachable')
        plan = RoutePlan(tuple(stops), now + back, spent, score)
        self._constraints.verify(plan, candidates, preferences, matrix)
        return plan
