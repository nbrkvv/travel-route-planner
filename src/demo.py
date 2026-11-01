"""Run with python demo.py; no third-party dependencies."""
from dataclasses import replace
from decimal import Decimal

from planner import (NearestNextStrategy, NoFeasibleRoute, Place, PreferenceFirstStrategy,
                     RankedPlace, RoutePlanner, TravelMatrix, TripPreferences)


def example() -> tuple[list[RankedPlace], TripPreferences, TravelMatrix]:
    candidates = [
        RankedPlace(Place('A', 'Парк', 40, Decimal('0'), 540, 1080), 0.4),
        RankedPlace(Place('B', 'Музей', 60, Decimal('500'), 540, 1080), 0.95),
        RankedPlace(Place('C', 'Галерея', 40, Decimal('300'), 540, 1080), 0.8),
    ]
    matrix = TravelMatrix({('S', 'A'): 5, ('S', 'B'): 20, ('S', 'C'): 15,
                           ('A', 'B'): 25, ('A', 'C'): 10, ('B', 'A'): 25,
                           ('B', 'C'): 10, ('C', 'A'): 10, ('C', 'B'): 10,
                           ('A', 'S'): 5, ('B', 'S'): 20, ('C', 'S'): 15})
    return candidates, TripPreferences('S', 'S', 540, 685, Decimal('800')), matrix


def clock(minute: int) -> str:
    return f'{minute // 60:02}:{minute % 60:02}'


def main() -> None:
    candidates, preferences, matrix = example()
    planner = RoutePlanner(NearestNextStrategy())
    for name, strategy in [('Ближайшая точка', NearestNextStrategy()),
                           ('Приоритет интересов', PreferenceFirstStrategy())]:
        planner.set_strategy(strategy)
        plan = planner.plan(candidates, preferences, matrix)
        print(f'\n{name}: ' + ' → '.join(stop.place.name for stop in plan.stops))
        for stop in plan.stops:
            print(f'  {clock(stop.arrival)} прибытие; '
                  f'{clock(stop.visit_start)}–{clock(stop.departure)} посещение')
        print(f'Возврат {clock(plan.finish_minute)}; стоимость {plan.total_cost} RUB; '
              f'оценка {plan.total_score:.2f}')
    try:
        planner.plan(candidates, replace(preferences, end_minute=550), matrix)
    except NoFeasibleRoute as error:
        print(f'\nОжидаемый отказ: {error}')


if __name__ == '__main__':
    main()
