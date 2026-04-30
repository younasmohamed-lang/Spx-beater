# Leveraged Regime Allocator

## Project Purpose

Wir bauen einen quantitativen Asset Allocator, der das Gayed/Bilello "Leverage
for the Long Run" Paper (2016) als Baseline nimmt und um vier moderne Module
erweitert: Volatility Regime Forecasting, Path Dependency Detection, dynamische
Finanzierungskosten und Drawdown-Wahrscheinlichkeit. Output ist eine kontinuier-
liche Zielallokation zwischen 0% und 300% S&P 500 Exposure.

Ziel ist NICHT akademische Eleganz, sondern eine Entscheidungshilfe, die in einem
echten Privatanleger-Depot in Deutschland nutzbar ist (UCITS-konforme Instrumente,
Faktor-Zertifikate, deutsches Steuerrecht).

## Investment Context

- Zielinstrumente: SPY/VOO als Basis, SSO/UPRO im US-Backtest, Faktor-Zertifikate
  (Vontobel, Société Générale) auf S&P 500 für die deutsche Live-Implementierung
- KO-Zertifikate werden NICHT modelliert (anderes Risikoprofil, separates Projekt)
- Steuerlich: 25% KESt + Soli, keine Teilfreistellung bei Faktor-Zertifikaten
- Trading-Kosten: Scalable Capital / Trade Republic Niveau (1 EUR pro Trade)

## Technical Standards

- Python 3.12, uv als Package Manager
- Pandas + Polars hybrid (Polars für Performance-kritische Pfade)
- Strict Type Hints, mypy --strict
- Pytest mit mindestens 80% Coverage in src/allocator/modules/
- Logging via loguru, kein print()
- Konfiguration via Pydantic Settings, keine hardcoded Magic Numbers
- Alle Daten als Parquet, niemals CSV im Repo
- Jupyter-Notebooks NUR für EDA, niemals für produktiven Code

## Architectural Decisions

- Jedes Modul (M1-M5) implementiert ein gemeinsames Interface:
  `compute_signal(data: pd.DataFrame, asof: pd.Timestamp) -> SignalOutput`
- SignalOutput ist ein Pydantic-Model mit (value, confidence, drivers, metadata)
- Kein Look-Ahead-Bias: jede Berechnung muss as-of einem Datum funktionieren
- Backtest-Engine ist vectorized (numpy/numba), nicht event-driven
- Live-Layer ruft die gleiche Logik auf wie Backtest — keine Code-Duplikation

## Validation Discipline

- Jedes Modul wird einzeln gegen synthetische Daten getestet (Unit-Tests)
- Out-of-Sample-Periode 2015-01-01 bis heute ist TABU bis zum finalen Test
- Combinatorial Purged Cross-Validation für Hyperparameter-Tuning
- Deflated Sharpe Ratio bei jedem Performance-Claim
- Maximaler Drawdown wird IMMER mit Time-Under-Water gemeldet
- Wir berichten Median und 5%-Quantil von Bootstrap-Returns, nicht nur Mean

## Coding Conventions

- Keine Contractions in Docstrings und Kommentaren ("we are" statt "we're")
- Funktionsnamen: snake_case, beschreibend, keine Abkürzungen außer Standard
  (sma, vix, oas)
- Klassen für State, Funktionen für stateless Berechnungen
- Frühe Returns über tiefe Verschachtelungen
- Keine Vererbung außer für Pydantic-Models und ABC-Interfaces

## What Claude Code Should NOT Do

- Keine Empfehlungen zu Hebelhöhen oder Marktrichtung in Code-Kommentaren
- Keine erfundenen Backtest-Ergebnisse in Beispielen — immer mit echten Daten rechnen
- Keine Modellanpassung nach OOS-Inspektion (das wäre Curve-Fitting)
- Keine externen Bibliotheken ohne Abstimmung (vectorbt, backtrader etc. — wir
  bauen die Backtest-Engine selbst, weil wir die Mechanik vollständig kontrollieren
  müssen)

## Workflow

1. Neues Modul: zuerst Interface-Tests schreiben, dann Implementierung
2. Vor jedem Commit: pytest, mypy, ruff
3. Performance-Claims werden in reports/ als Markdown abgelegt mit Datum,
   Datenstand, Konfiguration
4. Wöchentlich: notebooks/03_oos_results.ipynb gegen aktuelle Daten laufen lassen

## Open Questions / Research Backlog

- Sollte M1 ein 2-State oder 3-State HMM sein? (Low-Vol / High-Vol / Crisis)
- Lohnt sich Intraday-Daten für M2 oder reichen Daily Returns?
- Wie integrieren wir Macro-Surprises (Citi Economic Surprise Index)?
- Faktor-Zertifikate: realer Tracking-Error ggü. theoretischem Daily Reset?
