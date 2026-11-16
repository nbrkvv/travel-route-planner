"""Учебный прототип L4: построение городского туристического маршрута.

Python 3.10+. Стратегия определяет оценку допустимых вариантов маршрута.
Внешние API и база данных намеренно заменены подготовленным TripContext.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations


class NoFeasibleRoute(ValueError):
    """Нет маршрута, удовлетворяющего обязательным ограничениям."""


@dataclass(frozen=True)
class Place:
    name: str
    categories: tuple[str, ...]
    price: Decimal
    visit_minutes: int

    def __post_init__(self) -> None:
        if self.price < 0 or self.visit_minutes <= 0:
            raise ValueError("Стоимость и длительность посещения заданы неверно")


@dataclass(frozen=True)
class TripCriteria:
    interests: tuple[str, ...]
    budget: Decimal
    duration_limit: int
    max_places: int

    def __post_init__(self) -> None:
        if self.budget < 0 or self.duration_limit <= 0 or self.max_places <= 0:
            raise ValueError("Недопустимые ограничения маршрута")


@dataclass(frozen=True)
class TripContext:
    """Нормализованные данные адаптера; индекс 0 матриц — стартовая точка."""

    places: tuple[Place, ...]
    distances_m: tuple[tuple[float, ...], ...]
    durations_min: tuple[tuple[int, ...], ...]

    def validate(self) -> None:
        size = len(self.places) + 1
        for matrix in (self.distances_m, self.durations_min):
            if len(matrix) != size or any(len(row) != size for row in matrix):
                raise ValueError("Некорректная размерность матрицы перемещений")
            if any(value < 0 for row in matrix for value in row):
                raise ValueError("Отрицательные расстояния или время перемещения")


@dataclass(frozen=True)
class TripPlan:
    ordered_stops: tuple[Place, ...]
    total_distance_m: float
    total_duration_min: int
    estimated_cost: Decimal
    score: float


def relevance(plan: TripPlan, criteria: TripCriteria) -> float:
    """Доля остановок, совпадающих с интересами путешественника."""
    interests = {value.casefold() for value in criteria.interests}
    matches = sum(
        bool(interests.intersection(category.casefold() for category in stop.categories))
        for stop in plan.ordered_stops
    )
    return matches / len(plan.ordered_stops)


class RouteScoringStrategy(ABC):
    """Единый интерфейс алгоритмов оценки маршрута (Strategy)."""

    @abstractmethod
    def score(self, plan: TripPlan, criteria: TripCriteria) -> float:
        """Вернуть оценку: больше — лучше."""


class InterestFirstStrategy(RouteScoringStrategy):
    """Приоритет соответствия интересам пользователя."""

    def score(self, plan: TripPlan, criteria: TripCriteria) -> float:
        return (10.0 * relevance(plan, criteria)
                + 0.5 * len(plan.ordered_stops)
                - plan.total_distance_m / 10_000.0)


class ShortestRouteScoringStrategy(RouteScoringStrategy):
    """Приоритет минимальной длины маршрута."""

    def score(self, plan: TripPlan, criteria: TripCriteria) -> float:
        return -plan.total_distance_m


class BalancedRouteScoringStrategy(RouteScoringStrategy):
    """Компромисс интересов, расстояния и расходов."""

    def score(self, plan: TripPlan, criteria: TripCriteria) -> float:
        cost_share = (float(plan.estimated_cost / criteria.budget)
                      if criteria.budget > 0 else 0.0)
        return (0.60 * relevance(plan, criteria)
                - 0.25 * plan.total_distance_m / 5000.0
                - 0.15 * cost_share)


class TripPlanner:
    """Контекст стратегии: генерирует допустимые варианты и выбирает лучший."""

    def __init__(self, context: TripContext, strategy: RouteScoringStrategy) -> None:
        context.validate()
        self._context = context
        self._strategy = strategy

    def set_strategy(self, strategy: RouteScoringStrategy) -> None:
        """Сменить алгоритм без изменения механизма построения маршрутов."""
        self._strategy = strategy

    def build_trip(self, criteria: TripCriteria) -> TripPlan:
        """Контракт I2 ЛР №2: критерии -> оптимальный маршрут."""
        places = self._context.places
        if len(places) > 8 or criteria.max_places > 4:
            raise ValueError("Для демонстрации: максимум 8 мест и 4 остановки")

        best: TripPlan | None = None
        for count in range(1, min(len(places), criteria.max_places) + 1):
            for order in permutations(range(1, len(places) + 1), count):
                stops = tuple(places[index - 1] for index in order)
                cost = sum((place.price for place in stops), Decimal("0"))
                if cost > criteria.budget:
                    continue

                path = (0,) + order
                distance = sum(self._context.distances_m[a][b]
                               for a, b in zip(path, path[1:]))
                travel = sum(self._context.durations_min[a][b]
                             for a, b in zip(path, path[1:]))
                duration = travel + sum(place.visit_minutes for place in stops)
                if duration > criteria.duration_limit:
                    continue

                draft = TripPlan(stops, distance, duration, cost, 0.0)
                candidate = TripPlan(
                    stops, distance, duration, cost,
                    self._strategy.score(draft, criteria),
                )
                if best is None or candidate.score > best.score:
                    best = candidate

        if best is None:
            raise NoFeasibleRoute("Маршрут с заданными ограничениями не найден")
        return best


def main() -> None:
    """Ручной демонстрационный запуск; без автотестов и сетевых API."""
    context = TripContext(
        places=(
            Place("Музей", ("история",), Decimal("600"), 60),
            Place("Парк", ("природа",), Decimal("0"), 40),
            Place("Галерея", ("искусство",), Decimal("350"), 50),
        ),
        distances_m=(
            (0, 2000, 800, 1500),
            (2000, 0, 1000, 600),
            (800, 1000, 0, 1200),
            (1500, 600, 1200, 0),
        ),
        durations_min=(
            (0, 20, 8, 15),
            (20, 0, 10, 6),
            (8, 10, 0, 12),
            (15, 6, 12, 0),
        ),
    )
    criteria = TripCriteria(("история", "искусство"), Decimal("1000"), 145, 2)
    engine = TripPlanner(context, InterestFirstStrategy())
    strategies: tuple[RouteScoringStrategy, ...] = (
        InterestFirstStrategy(), ShortestRouteScoringStrategy(), BalancedRouteScoringStrategy(),
    )
    for strategy in strategies:
        engine.set_strategy(strategy)
        route = engine.build_trip(criteria)
        names = " -> ".join(place.name for place in route.ordered_stops)
        print(f"{type(strategy).__name__}: {names}; "
              f"{route.total_distance_m:.0f} м; {route.total_duration_min} мин; "
              f"{route.estimated_cost} руб.; score={route.score:.3f}")


if __name__ == "__main__":
    main()
